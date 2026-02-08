"""
Reddit data collector using **asyncpraw** (async Python Reddit API Wrapper).

Collects climate-related posts and top-level comments from UK-focused
subreddits.  Configured via environment variables.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

import asyncpraw  # type: ignore[import-untyped]
import asyncpraw.models  # type: ignore[import-untyped]

from app.core.config import settings
from collectors.base import BaseCollector, CollectedItem
from collectors.locations import find_locations


# Default subreddits to monitor.
_DEFAULT_SUBREDDITS: list[str] = [
    "ukpolitics",
    "climate",
    "unitedkingdom",
    "ukweather",
]


class RedditCollector(BaseCollector):
    """
    Collect climate-related discourse from Reddit using the official API
    via asyncpraw.

    Configuration
    -------------
    The following environment variables **must** be set:

    - ``REDDIT_CLIENT_ID``
    - ``REDDIT_CLIENT_SECRET``
    - ``REDDIT_USER_AGENT`` (optional, falls back to a sensible default)
    """

    def __init__(
        self,
        rate_limit_seconds: float = 2.0,
        subreddits: list[str] | None = None,
    ):
        super().__init__(source_name="reddit", rate_limit_seconds=rate_limit_seconds)
        self.subreddits = subreddits or _DEFAULT_SUBREDDITS

        # Validate Reddit credentials early.
        self._client_id = settings.REDDIT_CLIENT_ID
        self._client_secret = settings.REDDIT_CLIENT_SECRET
        self._user_agent = settings.REDDIT_USER_AGENT

        if not self._client_id or not self._client_secret:
            self.logger.warning(
                "REDDIT_CLIENT_ID and/or REDDIT_CLIENT_SECRET are not set. "
                "Reddit collection will fail at runtime."
            )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def collect(
        self,
        *,
        keywords: list[str] | None = None,
        max_posts_per_subreddit: int = 25,
        max_comments_per_post: int = 10,
        **kwargs,
    ) -> list[CollectedItem]:
        """
        Search configured subreddits for climate-related posts and collect
        both the post text and top-level comments.

        Parameters
        ----------
        keywords:
            Override the default climate keywords.
        max_posts_per_subreddit:
            Maximum posts to fetch per subreddit per keyword search.
        max_comments_per_post:
            Maximum top-level comments to collect per post.
        """
        search_terms = keywords or self.CLIMATE_KEYWORDS
        collected: list[CollectedItem] = []
        seen_ids: set[str] = set()

        reddit = asyncpraw.Reddit(
            client_id=self._client_id,
            client_secret=self._client_secret,
            user_agent=self._user_agent,
        )

        try:
            for sub_name in self.subreddits:
                self.logger.info("Reddit: processing r/%s", sub_name)
                try:
                    subreddit = await reddit.subreddit(sub_name)
                except Exception:
                    self.logger.exception("Reddit: could not access r/%s", sub_name)
                    continue

                for term in search_terms:
                    self.logger.debug("Reddit: searching r/%s for %r", sub_name, term)
                    try:
                        items = await self._search_subreddit(
                            subreddit=subreddit,
                            query=term,
                            sub_name=sub_name,
                            max_posts=max_posts_per_subreddit,
                            max_comments=max_comments_per_post,
                            seen_ids=seen_ids,
                        )
                        collected.extend(items)
                    except Exception:
                        self.logger.exception(
                            "Reddit: search failed for %r in r/%s", term, sub_name
                        )

                    await self._rate_limit()
        finally:
            await reddit.close()

        self.items_collected = len(collected)
        self.logger.info("Reddit: collected %d items total", len(collected))
        return collected

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _search_subreddit(
        self,
        *,
        subreddit: asyncpraw.models.Subreddit,
        query: str,
        sub_name: str,
        max_posts: int,
        max_comments: int,
        seen_ids: set[str],
    ) -> list[CollectedItem]:
        """Search a single subreddit and return collected items."""
        items: list[CollectedItem] = []

        async for submission in subreddit.search(query, sort="new", limit=max_posts):
            post_id = str(submission.id)
            if post_id in seen_ids:
                continue
            seen_ids.add(post_id)

            # -- Collect the post itself --------------------------------
            post_item = self._submission_to_item(submission, sub_name)
            if post_item is not None:
                items.append(post_item)

            # -- Collect top-level comments -----------------------------
            try:
                submission.comment_sort = "best"
                await submission.load()
                # Replace MoreComments objects so we only get actual comments.
                await submission.comments.replace_more(limit=0)

                for idx, comment in enumerate(submission.comments):  # type: ignore[union-attr]
                    if idx >= max_comments:
                        break
                    if not hasattr(comment, "body"):
                        continue

                    comment_item = self._comment_to_item(comment, submission, sub_name)
                    if comment_item is not None:
                        comment_id = str(comment.id)
                        if comment_id not in seen_ids:
                            seen_ids.add(comment_id)
                            items.append(comment_item)
            except Exception:
                self.logger.exception(
                    "Reddit: failed to load comments for post %s", post_id
                )

        return items

    # ------------------------------------------------------------------
    # Conversion helpers
    # ------------------------------------------------------------------

    def _submission_to_item(
        self,
        submission: asyncpraw.models.Submission,
        sub_name: str,
    ) -> Optional[CollectedItem]:
        """Convert a Reddit submission to a :class:`CollectedItem`."""
        title = str(getattr(submission, "title", "") or "")
        selftext = str(getattr(submission, "selftext", "") or "")
        content = selftext if selftext else title

        if not content or len(content.strip()) < 20:
            return None

        permalink = f"https://www.reddit.com{submission.permalink}"
        author_name = str(submission.author) if submission.author else None
        created_utc = _utc_from_timestamp(submission.created_utc)

        combined_text = f"{title} {content}"
        location_hints = [loc["name"] for loc in find_locations(combined_text)]

        return CollectedItem(
            title=title[:512] if title else "(no title)",
            content=content,
            source_url=permalink,
            author=author_name,
            published_at=created_utc,
            location_hints=location_hints,
            raw_metadata={
                "source": "reddit",
                "subreddit": sub_name,
                "post_id": str(submission.id),
                "score": int(getattr(submission, "score", 0)),
                "num_comments": int(getattr(submission, "num_comments", 0)),
                "upvote_ratio": float(getattr(submission, "upvote_ratio", 0.0)),
                "is_self": bool(getattr(submission, "is_self", True)),
                "link_flair_text": getattr(submission, "link_flair_text", None),
                "item_type": "post",
            },
        )

    def _comment_to_item(
        self,
        comment: asyncpraw.models.Comment,
        parent_submission: asyncpraw.models.Submission,
        sub_name: str,
    ) -> Optional[CollectedItem]:
        """Convert a Reddit comment to a :class:`CollectedItem`."""
        body = str(getattr(comment, "body", "") or "")
        if not body or len(body.strip()) < 20:
            return None

        # Use the parent post title as the item title.
        parent_title = str(getattr(parent_submission, "title", ""))
        permalink = f"https://www.reddit.com{comment.permalink}"
        author_name = str(comment.author) if comment.author else None
        created_utc = _utc_from_timestamp(comment.created_utc)

        location_hints = [loc["name"] for loc in find_locations(body)]

        return CollectedItem(
            title=f"[Comment] {parent_title}"[:512],
            content=body,
            source_url=permalink,
            author=author_name,
            published_at=created_utc,
            location_hints=location_hints,
            raw_metadata={
                "source": "reddit",
                "subreddit": sub_name,
                "post_id": str(parent_submission.id),
                "comment_id": str(comment.id),
                "score": int(getattr(comment, "score", 0)),
                "parent_id": str(getattr(comment, "parent_id", "")),
                "item_type": "comment",
            },
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_from_timestamp(ts: float | None) -> Optional[datetime]:
    """Convert a Unix timestamp to a timezone-aware UTC datetime."""
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    except (OSError, ValueError, OverflowError):
        return None
