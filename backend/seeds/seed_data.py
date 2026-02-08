"""
Seed data for the Thermoculture Research Assistant.
Contains 60+ sample discourse entries from various UK sources covering 2023-2024.
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from random import choice, uniform, randint

# ============================================================
# Location seed data
# ============================================================
LOCATIONS = [
    {"name": "London", "region": "LONDON", "latitude": 51.5074, "longitude": -0.1278},
    {"name": "Manchester", "region": "NORTH_WEST", "latitude": 53.4808, "longitude": -2.2426},
    {"name": "Birmingham", "region": "WEST_MIDLANDS", "latitude": 52.4862, "longitude": -1.8904},
    {"name": "Liverpool", "region": "NORTH_WEST", "latitude": 53.4084, "longitude": -2.9916},
    {"name": "Leeds", "region": "YORKSHIRE", "latitude": 53.8008, "longitude": -1.5491},
    {"name": "Sheffield", "region": "YORKSHIRE", "latitude": 53.3811, "longitude": -1.4701},
    {"name": "Bristol", "region": "SOUTH_WEST", "latitude": 51.4545, "longitude": -2.5879},
    {"name": "Edinburgh", "region": "SCOTLAND", "latitude": 55.9533, "longitude": -3.1883},
    {"name": "Glasgow", "region": "SCOTLAND", "latitude": 55.8642, "longitude": -4.2518},
    {"name": "Cardiff", "region": "WALES", "latitude": 51.4816, "longitude": -3.1791},
    {"name": "Belfast", "region": "NORTHERN_IRELAND", "latitude": 54.5973, "longitude": -5.9301},
    {"name": "Newcastle", "region": "NORTH_EAST", "latitude": 54.9783, "longitude": -1.6178},
    {"name": "Nottingham", "region": "EAST_MIDLANDS", "latitude": 52.9548, "longitude": -1.1581},
    {"name": "Brighton", "region": "SOUTH_EAST", "latitude": 50.8225, "longitude": -0.1372},
    {"name": "Oxford", "region": "SOUTH_EAST", "latitude": 51.7520, "longitude": -1.2577},
    {"name": "Cambridge", "region": "EAST", "latitude": 52.2053, "longitude": 0.1218},
    {"name": "York", "region": "YORKSHIRE", "latitude": 53.9591, "longitude": -1.0815},
    {"name": "Bath", "region": "SOUTH_WEST", "latitude": 51.3811, "longitude": -2.3590},
    {"name": "Norwich", "region": "EAST", "latitude": 52.6309, "longitude": 1.2974},
    {"name": "Exeter", "region": "SOUTH_WEST", "latitude": 50.7184, "longitude": -3.5339},
    {"name": "Plymouth", "region": "SOUTH_WEST", "latitude": 50.3755, "longitude": -4.1427},
    {"name": "Aberdeen", "region": "SCOTLAND", "latitude": 57.1497, "longitude": -2.0943},
    {"name": "Dundee", "region": "SCOTLAND", "latitude": 56.4620, "longitude": -2.9707},
    {"name": "Swansea", "region": "WALES", "latitude": 51.6214, "longitude": -3.9436},
    {"name": "Coventry", "region": "WEST_MIDLANDS", "latitude": 52.4068, "longitude": -1.5197},
]

# ============================================================
# Source seed data
# ============================================================
SOURCES = [
    {"name": "BBC News", "source_type": "NEWS", "url": "https://www.bbc.co.uk/news", "description": "BBC News climate coverage"},
    {"name": "The Guardian", "source_type": "NEWS", "url": "https://www.theguardian.com/uk", "description": "Guardian UK environment and climate section"},
    {"name": "r/unitedkingdom", "source_type": "REDDIT", "url": "https://reddit.com/r/unitedkingdom", "description": "UK general discussion subreddit"},
    {"name": "r/ukpolitics", "source_type": "REDDIT", "url": "https://reddit.com/r/ukpolitics", "description": "UK political discussion subreddit"},
    {"name": "r/climate", "source_type": "REDDIT", "url": "https://reddit.com/r/climate", "description": "Climate discussion subreddit"},
    {"name": "Manchester Evening News", "source_type": "NEWS", "url": "https://www.manchestereveningnews.co.uk", "description": "Regional news - Manchester"},
    {"name": "Yorkshire Post", "source_type": "NEWS", "url": "https://www.yorkshirepost.co.uk", "description": "Regional news - Yorkshire"},
    {"name": "The Scotsman", "source_type": "NEWS", "url": "https://www.scotsman.com", "description": "Scottish national newspaper"},
    {"name": "Wales Online", "source_type": "NEWS", "url": "https://www.walesonline.co.uk", "description": "Welsh news source"},
    {"name": "Manual Research Entries", "source_type": "MANUAL", "url": None, "description": "Manually entered discourse samples from field research"},
]

# ============================================================
# Theme seed data
# ============================================================
THEMES = [
    {"name": "Heatwave", "description": "Intense heat events and their impacts", "category": "Environmental"},
    {"name": "Thermal Inequality", "description": "Disproportionate impacts of heat on different social groups", "category": "Social"},
    {"name": "Thermal", "description": "General discussions about temperature and heat", "category": "General"},
    {"name": "Heating", "description": "Home heating, appliances, and energy usage", "category": "Practical"},
    {"name": "Urban Heat Island", "description": "Heat retention in built-up urban environments", "category": "Environmental"},
    {"name": "Community Action", "description": "Local groups and grassroots initiatives", "category": "Social"},
    {"name": "Energy and Heating", "description": "Intersection of energy costs and thermal comfort", "category": "Economic"},
    {"name": "Extreme Weather", "description": "Heatwaves, storms, and other climate extremes", "category": "Environmental"},
    {"name": "Housing and Buildings", "description": "Infrastructure, retrofit, and building standards", "category": "Practical"},
    {"name": "Mental Health and Anxiety", "description": "Emotional and psychological responses to climate change", "category": "Social"},
    {"name": "Cities (Climate Change)", "description": "Urban planning and resilience in the context of climate change", "category": "Environmental"},
    {"name": "Policy and Governance", "description": "Regulation, targets, and government action", "category": "Political"},
]

# ============================================================
# Discourse samples - 60+ entries
# ============================================================
DISCOURSE_SAMPLES = [
    # === NEWS ARTICLES ===
    {
        "title": "London heatwave: Temperatures soar above 35°C as city swelters",
        "content": "London experienced its hottest day of 2024 yesterday as temperatures soared above 35°C across the capital. The Met Office issued an amber heat warning covering much of southeast England. Transport for London reported significant disruption as rails buckled in the extreme heat, while hospitals reported a surge in heat-related admissions. Londoners flocked to parks and open water swimming spots to cool down. Climate scientists warn that such extreme heat events are becoming more frequent and intense due to climate change, with urban heat island effects making London particularly vulnerable. The city's aging infrastructure, designed for a cooler climate, is increasingly strained by these events.",
        "source_idx": 0, "location_idx": 0, "author": "BBC News Climate Team",
        "themes": ["Extreme Weather", "Cities (Climate Change)"], "sentiment": -0.35, "classification": "PRACTICAL_ADAPTATION",
        "date_offset_days": -180,
    },
    {
        "title": "Manchester flooding leaves hundreds of homes underwater after Storm Babet",
        "content": "Hundreds of homes in Greater Manchester have been left underwater following Storm Babet, which brought record rainfall to the region over the weekend. The River Irwell burst its banks in several locations, flooding streets in Salford and parts of the city centre. Residents described scenes of devastation as water levels rose rapidly overnight. 'We've never seen anything like this,' said Margaret Thompson, 72, from Broughton. 'The water came up so fast we barely had time to move our things upstairs.' The Environment Agency had issued severe flood warnings but the scale of flooding exceeded predictions. Manchester City Council has opened emergency shelters and is coordinating the response. Questions are being raised about the adequacy of flood defences and whether climate change is making such events more likely.",
        "source_idx": 5, "location_idx": 1, "author": "Tom Richards",
        "themes": ["Extreme Weather", "Community Action"], "sentiment": -0.65, "classification": "EMOTIONAL_RESPONSE",
        "date_offset_days": -220,
    },
    {
        "title": "Scotland leads UK in renewable energy with 97% of electricity from clean sources",
        "content": "Scotland has generated 97% of its electricity from renewable sources in the first half of 2024, according to new figures from the Scottish Government. Wind power accounted for the majority of generation, with Scotland's onshore and offshore wind farms producing enough electricity to power every home in Scotland twice over. First Minister praised the achievement but acknowledged more work is needed on heating and transport decarbonisation. The Scottish Government has set a target of net zero emissions by 2045, five years ahead of the UK-wide target. Critics argue that while electricity generation is impressive, Scotland still relies heavily on oil and gas for heating and industrial processes. Community energy projects across the Highlands and Islands have been particularly successful, with local ownership models providing economic benefits to rural communities.",
        "source_idx": 7, "location_idx": 7, "author": "The Scotsman Environment Desk",
        "themes": ["Policy and Governance", "Energy and Heating", "Community Action"], "sentiment": 0.72, "classification": "POLICY_DISCUSSION",
        "date_offset_days": -90,
    },
    {
        "title": "Welsh farmers struggle as changing climate disrupts traditional farming calendar",
        "content": "Farmers across Wales are reporting significant disruption to their traditional farming calendars as climate change alters weather patterns. In the Brecon Beacons, sheep farmers say lambing season has become unpredictable, with warmer winters confusing the natural cycle. 'My grandfather knew exactly when to expect lambing based on centuries of tradition,' said Dai Evans, a third-generation farmer from Llandeilo. 'Now the seasons are all over the place.' Crop farmers in Pembrokeshire report problems with both drought and waterlogging, sometimes in the same season. The National Farmers' Union Cymru is calling for more government support for climate adaptation measures, including investment in water management infrastructure and new crop varieties suited to changing conditions. Some farmers are experimenting with Mediterranean crops that were previously impossible to grow in Wales.",
        "source_idx": 8, "location_idx": 9, "author": "Wales Online Rural Affairs",
        "themes": ["Policy and Governance", "Extreme Weather"], "sentiment": -0.42, "classification": "PRACTICAL_ADAPTATION",
        "date_offset_days": -150,
    },
    {
        "title": "Birmingham council approves £500m retrofit programme for social housing",
        "content": "Birmingham City Council has approved a landmark £500 million programme to retrofit its entire social housing stock with energy efficiency measures. The scheme, one of the largest in Europe, will see 60,000 council homes fitted with insulation, heat pumps, and solar panels over the next decade. Council leader described it as 'the biggest investment in our housing stock since the estates were built.' Residents in pilot areas report energy bill savings of up to 60%, with improved comfort and reduced damp. The programme is expected to create 5,000 green jobs in the West Midlands. However, some residents have expressed concerns about disruption during installation and the performance of heat pumps in older properties. The scheme is being funded through a combination of government grants, council borrowing, and expected energy savings.",
        "source_idx": 0, "location_idx": 2, "author": "BBC News Midlands",
        "themes": ["Housing and Buildings", "Energy and Heating"], "sentiment": 0.55, "classification": "POLICY_DISCUSSION",
        "date_offset_days": -60,
    },
    {
        "title": "Yorkshire Dales face water crisis as reservoirs drop to record lows",
        "content": "Water companies across Yorkshire have declared a drought after reservoir levels dropped to their lowest point in 30 years. Yorkshire Water has implemented a hosepipe ban affecting over 5 million customers. The company says that despite recent rain, reservoir levels remain critically low at just 35% capacity. Farmers in the Dales are struggling to water livestock, with some having to transport water by tanker to remote hill farms. Environmental groups say the crisis exposes decades of underinvestment in water infrastructure and the failure to plan for climate change. The River Wharfe and several other waterways have dried up in sections, devastating fish populations. 'We used to take water for granted in Yorkshire,' said one local farmer. 'Those days are gone.' The Environment Agency is working with farmers to manage water resources but acknowledges the situation is unprecedented.",
        "source_idx": 6, "location_idx": 4, "author": "Yorkshire Post Environment Correspondent",
        "themes": ["Extreme Weather"], "sentiment": -0.58, "classification": "PRACTICAL_ADAPTATION",
        "date_offset_days": -200,
    },
    {
        "title": "Bristol becomes first UK city to declare climate emergency complete",
        "content": "Bristol has become the first major UK city to claim it has met its initial climate emergency targets, reducing carbon emissions by 45% from 2005 levels. The city credits a combination of active transport infrastructure, building retrofits, and a shift to renewable energy. The Bristol One City Climate Strategy has been held up as a model for other cities. Mayor's office released data showing cycling has increased by 300% since 2015, while bus usage is at record levels following the introduction of a mass transit system. Critics argue the figures don't account for consumption-based emissions and that much of the reduction comes from deindustrialisation rather than active policy. Nevertheless, the city has attracted significant green investment and tech companies citing its environmental credentials.",
        "source_idx": 1, "location_idx": 6, "author": "Guardian Cities",
        "themes": ["Policy and Governance", "Cities (Climate Change)", "Community Action"], "sentiment": 0.61, "classification": "POLICY_DISCUSSION",
        "date_offset_days": -45,
    },
    {
        "title": "Newcastle residents battle plans for new coal mine despite climate commitments",
        "content": "Residents in the Newcastle area are mobilising against proposals for a new opencast coal mine in Northumberland, arguing it contradicts the UK's climate commitments. The planning application, submitted by mining firm UK Coal, would extract 3 million tonnes of coal over 15 years. Local campaign group Coal Action Network has gathered over 10,000 signatures opposing the mine. 'It's absurd that we're even considering new coal extraction when we're supposed to be reaching net zero,' said campaign spokesperson Ruth Henderson. Supporters of the mine argue it would create 200 jobs in an area of high unemployment and that the coal is needed for steel production. The decision has become a flashpoint in the debate between economic need and climate action in former mining communities.",
        "source_idx": 0, "location_idx": 11, "author": "BBC News North East",
        "themes": ["Policy and Governance", "Community Action"], "sentiment": -0.38, "classification": "COMMUNITY_ACTION",
        "date_offset_days": -130,
    },
    {
        "title": "Brighton leads surge in community energy projects across South East",
        "content": "Brighton has emerged as a hub for community energy projects, with over 30 community-owned solar installations now operating across the city. Brighton Energy Co-operative, the largest community energy organisation in the South East, has raised £4 million from local investors to fund solar panels on schools, community centres, and social housing. Members receive a return on their investment while reducing carbon emissions. The model is being replicated across the region, with community groups in Lewes, Worthing, and Hastings all launching their own projects. 'Community energy puts power literally in people's hands,' said co-op director Emma Davies. 'It shows that climate action doesn't have to be top-down.' The government's recent changes to planning rules for rooftop solar have given the sector a significant boost.",
        "source_idx": 1, "location_idx": 13, "author": "Guardian Environment",
        "themes": ["Energy and Heating", "Community Action"], "sentiment": 0.68, "classification": "COMMUNITY_ACTION",
        "date_offset_days": -75,
    },
    {
        "title": "Oxford study reveals growing eco-anxiety among UK teenagers",
        "content": "A major study by Oxford University researchers has found that 75% of UK teenagers experience some form of climate anxiety, with 25% reporting it significantly affects their daily lives. The study, published in The Lancet Planetary Health, surveyed 10,000 young people aged 13-19 across all UK regions. Researchers found that climate anxiety was highest in urban areas and among young women. Many respondents reported feelings of helplessness, anger at older generations, and fear for their future. Dr Sarah Chen, lead researcher, said: 'This is not just worry - it is a rational response to a real threat that is being validated by the extreme weather these young people are experiencing.' The study recommends schools integrate climate psychology into their curricula and that the NHS develop specific support pathways for eco-anxiety.",
        "source_idx": 1, "location_idx": 14, "author": "Guardian Health",
        "themes": ["Mental Health and Anxiety"], "sentiment": -0.48, "classification": "EMOTIONAL_RESPONSE",
        "date_offset_days": -30,
    },
    {
        "title": "Nottingham tram network expansion praised as model for urban decarbonisation",
        "content": "Nottingham's expanded tram network has been praised by transport experts as a model for how UK cities can decarbonise urban transport. The city's third tram line, opened earlier this year, has exceeded ridership projections by 40%. Car journeys in the city centre have decreased by 15% since the expansion. The electric trams run on 100% renewable energy and have been integrated with an extensive park-and-ride network. Nottingham also became the first UK city to introduce a workplace parking levy, which has funded further public transport improvements. 'Nottingham proves that with political will and smart investment, you can shift people out of cars,' said transport researcher Dr Michael Ward. The success has prompted several other cities, including Leicester and Derby, to explore similar schemes.",
        "source_idx": 0, "location_idx": 12, "author": "BBC News East Midlands",
        "themes": ["Cities (Climate Change)", "Policy and Governance"], "sentiment": 0.65, "classification": "POLICY_DISCUSSION",
        "date_offset_days": -100,
    },
    {
        "title": "Glasgow tenements face mould crisis as damp winters become the norm",
        "content": "Thousands of tenement residents in Glasgow are battling worsening mould and damp as milder, wetter winters become increasingly common. Housing campaigners say the city's Victorian-era tenements, home to over 200,000 people, were not designed for the current climate conditions. Rising moisture levels combined with poor ventilation and inadequate insulation have created perfect conditions for black mould. 'Every winter it gets worse,' said tenant Fiona MacLeod from Partick. 'The walls are running with condensation. My children are constantly sick.' Glasgow City Council says it is working to address the problem but that the scale of the challenge is enormous, with an estimated 40,000 properties affected. The Scottish Government has pledged additional funding for tenement retrofit but campaigners say it falls far short of what is needed.",
        "source_idx": 7, "location_idx": 8, "author": "The Scotsman Housing",
        "themes": ["Housing and Buildings", "Thermal Inequality"], "sentiment": -0.62, "classification": "PRACTICAL_ADAPTATION",
        "date_offset_days": -160,
    },
    {
        "title": "Cambridge researchers develop drought-resistant wheat variety",
        "content": "Scientists at the University of Cambridge have developed a new wheat variety that can withstand extended periods of drought while maintaining yields. The breakthrough, published in Nature Plants, could help UK farmers adapt to increasingly dry summers. The new variety, dubbed 'CamDry-1', uses 40% less water than conventional wheat while producing comparable yields in trials across East Anglia. Lead researcher Professor James Mitchell said the work was driven by the 2022 drought that devastated UK wheat harvests. 'UK farmers need crops that can cope with our changing climate. Traditional varieties were bred for reliability in a stable climate we no longer have.' The variety is expected to be available commercially within three years, pending regulatory approval. Trials are being extended to other regions of the UK.",
        "source_idx": 1, "location_idx": 15, "author": "Guardian Science",
        "themes": ["Extreme Weather"], "sentiment": 0.58, "classification": "PRACTICAL_ADAPTATION",
        "date_offset_days": -40,
    },
    {
        "title": "Belfast flood defences fail again as climate investment gap widens",
        "content": "Belfast experienced severe flooding for the third time in two years after heavy rainfall overwhelmed the city's drainage system. Areas along the River Lagan including the Ormeau Road and parts of East Belfast saw water entering homes and businesses. The Northern Ireland Assembly has been criticised for underinvesting in flood defences despite repeated warnings from climate scientists. Infrastructure Minister acknowledged that the city's Victorian-era drainage system is not fit for purpose in an era of more intense rainfall. 'We need billions of pounds of investment and we need it now,' said environmental campaigner Ciaran O'Neill. Business owners on the Ormeau Road say they are struggling to get flood insurance and some are considering relocating. The flooding has reignited debate about climate adaptation priorities in Northern Ireland.",
        "source_idx": 0, "location_idx": 10, "author": "BBC News Northern Ireland",
        "themes": ["Extreme Weather", "Policy and Governance"], "sentiment": -0.71, "classification": "POLICY_DISCUSSION",
        "date_offset_days": -110,
    },
    {
        "title": "Devon community creates UK's first climate-adapted village",
        "content": "The village of Moretonhampstead in Devon has become what its residents call the UK's first 'climate-adapted village'. Over five years, the community has implemented a comprehensive adaptation plan including community-owned solar and battery storage, a rainwater harvesting network, a community food garden, and a natural flood management scheme using upstream tree planting. The project, funded by a combination of grants and community investment, has reduced the village's carbon footprint by 70% while making it more resilient to extreme weather. 'We got tired of waiting for the government to act,' said project coordinator Jenny Barrow. 'We decided to do it ourselves.' The village has become a pilgrimage site for community groups from across the UK wanting to replicate the model. The Devon model is now being studied by DEFRA as a potential template for rural climate adaptation.",
        "source_idx": 1, "location_idx": 19, "author": "Guardian Rural Network",
        "themes": ["Community Action", "Energy and Heating"], "sentiment": 0.78, "classification": "COMMUNITY_ACTION",
        "date_offset_days": -55,
    },

    # === REDDIT POSTS ===
    {
        "title": "Is anyone else's energy bill absolutely mental this winter?",
        "content": "Just got my energy bill through and it's gone up another 20% from last year. We already had the loft insulated and got a smart thermostat but it barely makes a difference. The house is a 1930s semi in Sheffield and it's like trying to heat a colander. Has anyone actually had a heat pump installed? Our gas boiler is on its last legs and I'm trying to work out if it's worth the massive upfront cost. The government grant barely covers a quarter of it. I feel like ordinary people are being asked to bear the cost of net zero while energy companies rake in record profits. Would love to hear from anyone who's actually made the switch.",
        "source_idx": 2, "location_idx": 5, "author": "u/SheffieldSteel_42",
        "themes": ["Energy and Heating", "Housing and Buildings"], "sentiment": -0.45, "classification": "PRACTICAL_ADAPTATION",
        "date_offset_days": -25,
    },
    {
        "title": "Just back from volunteering with flood cleanup in Carlisle. Absolutely devastating.",
        "content": "Spent the weekend volunteering with the flood cleanup in Carlisle. The scale of destruction is hard to comprehend until you see it. Entire ground floors of homes destroyed. People's belongings piled up in skips on the street. The smell is awful. Met one elderly couple who've been flooded three times in ten years. They can't sell their house, can't get insurance, and can't afford to move. They're basically trapped. The community spirit was incredible though - people from all over Cumbria coming to help, local businesses donating supplies. But you can't help thinking this is going to keep happening and getting worse. When is the government going to actually invest in proper flood defences for these communities?",
        "source_idx": 2, "location_idx": None, "author": "u/LakeDistrictLass",
        "themes": ["Extreme Weather", "Community Action"], "sentiment": -0.52, "classification": "EMOTIONAL_RESPONSE",
        "date_offset_days": -85,
    },
    {
        "title": "The ULEZ expansion is actually working and I hate that no one talks about it",
        "content": "I know ULEZ is politically toxic but the data is really clear - air quality in outer London has improved significantly since the expansion. NO2 levels are down 20% in areas that were previously above legal limits. My kid has asthma and for the first time in years she didn't need her inhaler daily through winter. I get that it's a cost burden for some people but the health benefits are real and measurable. Why aren't we talking about the fact that a climate/air quality policy is actually working? Is it because no political party wants to own it?",
        "source_idx": 3, "location_idx": 0, "author": "u/ZoneSixResident",
        "themes": ["Cities (Climate Change)", "Policy and Governance"], "sentiment": 0.35, "classification": "POLICY_DISCUSSION",
        "date_offset_days": -15,
    },
    {
        "title": "Climate change is a hoax pushed by the elite to control us. Change my mind.",
        "content": "Seriously, the climate has always changed. We had the Medieval Warm Period, the Little Ice Age. The Earth naturally goes through cycles. Now suddenly we're supposed to destroy our economy, give up our cars, freeze in our homes, and eat bugs because some computer models say it might get a bit warmer? Follow the money - who benefits from all this green hysteria? The same people selling you heat pumps and electric cars. Meanwhile China and India pump out more CO2 in a week than we save in a year. It's all about control and taxation dressed up as saving the planet. The ordinary working person is being squeezed to pay for middle-class virtue signalling.",
        "source_idx": 3, "location_idx": None, "author": "u/CommonSenseNotDead",
        "themes": ["Policy and Governance"], "sentiment": -0.75, "classification": "DENIAL_DISMISSAL",
        "date_offset_days": -140,
    },
    {
        "title": "Our community garden in Liverpool is actually changing the neighbourhood",
        "content": "Two years ago a group of us took over an abandoned lot in Toxteth and turned it into a community food garden. We now grow enough veg to supply a weekly community stall and we've started composting food waste from local restaurants. But the real impact has been social - we've got retired people, refugees, young families all working together. Last summer we ran climate workshops for kids during school holidays. One of the local schools now does regular sessions with us. It started as a way to grow some tomatoes and it's become this amazing community hub that's also reducing food miles and waste. If anyone in Liverpool wants to get involved or start something similar in their area, DM me.",
        "source_idx": 2, "location_idx": 3, "author": "u/ToxtethGreenThumb",
        "themes": ["Community Action"], "sentiment": 0.82, "classification": "COMMUNITY_ACTION",
        "date_offset_days": -50,
    },
    {
        "title": "I had a panic attack thinking about climate change and I'm 35 years old",
        "content": "I know this might sound dramatic but I genuinely had a panic attack last week reading about the Antarctic ice sheet data. I'm 35, I have two kids under 5, and I just couldn't stop thinking about what kind of world they're going to inherit. I've been following climate science for years and every report seems worse than the last. I try to do my bit - we cycle everywhere, grow our own food, switched to a green energy tariff - but it feels completely inadequate against the scale of the problem. My GP has referred me to talking therapy but there's a 6-month wait. Is there a name for this? Is anyone else experiencing this? I feel like I'm losing my mind while everyone around me just carries on as normal.",
        "source_idx": 4, "location_idx": 6, "author": "u/BristolDad_Anxious",
        "themes": ["Mental Health and Anxiety"], "sentiment": -0.72, "classification": "EMOTIONAL_RESPONSE",
        "date_offset_days": -35,
    },
    {
        "title": "Electric car owners of the UK - honest review after 2 years?",
        "content": "Been thinking about making the switch to EV for our family car. We're in Norwich and do mainly city driving with occasional trips to London. Currently running a diesel Focus that costs a fortune in fuel. Would love to hear from actual owners about: real-world range in British weather (not the manufacturer claims), charging infrastructure outside of London, running costs vs petrol/diesel, and any issues with battery degradation. Also curious about those who've had solar panels installed and charge from those - does it actually work out economically? The whole thing feels like a minefield of conflicting information.",
        "source_idx": 2, "location_idx": 18, "author": "u/NorwichDriving",
        "themes": ["Cities (Climate Change)", "Energy and Heating"], "sentiment": 0.1, "classification": "PRACTICAL_ADAPTATION",
        "date_offset_days": -20,
    },
    {
        "title": "The government's net zero strategy is a complete joke",
        "content": "Just read the latest Committee on Climate Change report and it's damning. We're off track on virtually every metric. Housing retrofit targets are being missed by miles. Heat pump installations are a fraction of what's needed. Public transport investment outside London is pathetic. And now they're approving new oil and gas licences in the North Sea? You couldn't make it up. The gap between the rhetoric and the reality is staggering. Both major parties talk about net zero but neither has a credible plan to get there. Meanwhile we've just had the hottest summer on record and flooding is becoming an annual event. At what point does someone actually do something?",
        "source_idx": 3, "location_idx": None, "author": "u/PolicyWonkUK",
        "themes": ["Policy and Governance", "Housing and Buildings"], "sentiment": -0.68, "classification": "POLICY_DISCUSSION",
        "date_offset_days": -8,
    },
    {
        "title": "Moved back to rural Scotland and the biodiversity loss is shocking",
        "content": "Grew up near Inverness, moved to London for 15 years, just moved back. The change in wildlife is genuinely shocking. When I was a kid there were curlews, lapwings, and corncrakes in the fields around our village. Now they're gone. The River Ness used to be full of salmon - the fishermen say catches have collapsed. Even the insect populations seem noticeably reduced - remember driving in summer and having to clean your windscreen? That barely happens now. The old timers in the village all say the same thing. Meanwhile the hills are covered in non-native sitka spruce monoculture that's basically a green desert. I know climate change isn't the only factor but it's accelerating everything. Really makes you think about what we're losing.",
        "source_idx": 2, "location_idx": None, "author": "u/HighlandsReturn",
        "themes": ["Extreme Weather"], "sentiment": -0.55, "classification": "EMOTIONAL_RESPONSE",
        "date_offset_days": -65,
    },
    {
        "title": "Our school's climate strike actually got the council to act!",
        "content": "So our school in Leeds organised a climate strike last month. About 200 students walked out (with parent permission) and marched to the town hall. We presented a petition with 3,000 signatures asking the council to: plant 10,000 trees by 2025, make all school meals have a plant-based option, and create safe cycling routes to every school. I honestly thought nothing would come of it but the council leader actually met with us and last week they announced they're committing to all three demands! I'm 16 and this is the first time I've felt like adults are actually listening. It's not enough obviously but it shows that direct action works. If your school hasn't done something similar, please consider it.",
        "source_idx": 4, "location_idx": 4, "author": "u/LeedsClimateYouth",
        "themes": ["Community Action"], "sentiment": 0.75, "classification": "COMMUNITY_ACTION",
        "date_offset_days": -42,
    },
    {
        "title": "Anyone else noticed the seasons are completely off this year?",
        "content": "Is it just me or has anyone else in the UK noticed the seasons are completely muddled? I'm in Edinburgh and my daffodils came up in January, there were butterflies in February, and we had frost in May. My allotment is chaos - nothing is growing when it should. The cherry trees on my street blossomed three weeks early and then got hit by a late frost so there's no fruit. I've been gardening for 30 years and I've never seen anything like the last two or three years. The old rules about when to plant and when to harvest just don't apply anymore. Anyone else experiencing this? What are you doing differently?",
        "source_idx": 2, "location_idx": 7, "author": "u/EdinburghAllotment",
        "themes": ["Extreme Weather"], "sentiment": -0.38, "classification": "PRACTICAL_ADAPTATION",
        "date_offset_days": -28,
    },
    {
        "title": "Welsh Government banning new road building is the right call",
        "content": "Unpopular opinion apparently but the Welsh Government's decision to stop building new roads and invest in public transport instead is exactly the right thing to do. You cannot build your way out of congestion - it's induced demand. Every new road fills up within years. Meanwhile rail services in Wales are a joke and bus routes keep getting cut. The money needs to go where it actually reduces emissions and improves people's lives. Yes it's inconvenient in the short term but so is a climate catastrophe. The Netherlands didn't become a cycling paradise overnight. Cardiff is already seeing the benefits of the new active travel routes. Sometimes you need politicians brave enough to make the unpopular but necessary decisions.",
        "source_idx": 3, "location_idx": 9, "author": "u/WelshTransportNerd",
        "themes": ["Cities (Climate Change)", "Policy and Governance"], "sentiment": 0.42, "classification": "POLICY_DISCUSSION",
        "date_offset_days": -18,
    },
    {
        "title": "Insulated my Victorian terrace - here's what actually worked and what was a waste",
        "content": "After two years and way too much money, I've finally finished insulating our Victorian terrace in Bath. Here's my honest assessment: Internal wall insulation (the aerogel stuff) - expensive but genuinely transformative. Reduced heat loss through walls by about 60%. Loft insulation - cheap and effective, should have done this first. Underfloor insulation - nightmare to install in a Victorian house, moderate improvement. Secondary glazing - good compromise when you can't change listed windows. Draft-proofing - best bang for buck by far, spent £200 and saved probably £300/year. Heat pump - installed an air source unit. Works well in spring/autumn but struggles in deep winter. We still need the gas boiler as backup. Total cost: about £35,000 with grants covering £8,000. Energy bills down roughly 45%. Payback period: depressingly long. But the house is actually comfortable now, which is priceless.",
        "source_idx": 2, "location_idx": 17, "author": "u/BathVictorianOwner",
        "themes": ["Housing and Buildings", "Energy and Heating"], "sentiment": 0.32, "classification": "PRACTICAL_ADAPTATION",
        "date_offset_days": -12,
    },

    # === FORUM & SOCIAL MEDIA ===
    {
        "title": "Plymouth fishermen report unprecedented changes in marine life",
        "content": "Fishermen working out of Plymouth harbour are reporting dramatic changes in the species they're catching. Traditionally cold-water species like cod and haddock have become increasingly rare, while warm-water species including anchovies, sea bass, and even the occasional trigger fish are now regularly caught. 'Twenty years ago you'd never see a trigger fish in the Channel,' said skipper Dave Penrose, who has fished out of Plymouth for 35 years. 'Now we get them regularly.' Marine biologists at Plymouth Marine Laboratory say the changes are consistent with warming sea temperatures, which have risen by 1.2°C in the English Channel over the past three decades. The shift is forcing fishermen to adapt their gear and techniques, and is changing what appears on dinner plates across the South West.",
        "source_idx": 0, "location_idx": 20, "author": "BBC News Devon",
        "themes": ["Extreme Weather", "Policy and Governance"], "sentiment": -0.3, "classification": "PRACTICAL_ADAPTATION",
        "date_offset_days": -170,
    },
    {
        "title": "Coventry's electric bus fleet slashes city centre emissions",
        "content": "Coventry has replaced its entire city centre bus fleet with electric vehicles, becoming the first UK city outside London to achieve a fully electric urban bus network. The 130 electric buses, manufactured locally by Alexander Dennis, have reduced bus-related emissions by 100% and noise pollution significantly. Passengers report a noticeably quieter and more pleasant experience. The project was part of the City of Culture legacy programme and was funded by a combination of government transport grants and local authority investment. 'This shows what's possible when you combine ambition with investment,' said the transport secretary during a visit to the depot. Running costs are 60% lower than diesel equivalents, and the fleet is charged overnight using renewable energy. Other cities including Leicester and Wolverhampton are now exploring similar conversions.",
        "source_idx": 0, "location_idx": 24, "author": "BBC News West Midlands",
        "themes": ["Cities (Climate Change)", "Policy and Governance"], "sentiment": 0.7, "classification": "POLICY_DISCUSSION",
        "date_offset_days": -95,
    },
    {
        "title": "The hosepipe ban in Sussex has really opened my eyes",
        "content": "Never thought I'd see a hosepipe ban in England lasting three months. But here we are in Brighton and the garden is brown, the car is filthy, and my kids can't use the paddling pool. It's made me properly think about water for the first time. We've installed two water butts, started mulching the garden beds, and I'm looking at drought-resistant plants for next year. My neighbour has gone further and installed a grey water recycling system. The thing is, Southern Water has been dumping sewage in the sea AND telling us to save water. The hypocrisy is breathtaking. But the underlying problem is real - the South East is genuinely running out of water and we need to completely rethink how we use it.",
        "source_idx": 2, "location_idx": 13, "author": "u/BrightonBeachBum",
        "themes": ["Extreme Weather"], "sentiment": -0.35, "classification": "PRACTICAL_ADAPTATION",
        "date_offset_days": -190,
    },
    {
        "title": "Aberdeen offshore workers: the 'just transition' is a lie",
        "content": "I've worked offshore in the North Sea oil and gas industry for 18 years. The politicians keep talking about a 'just transition' to renewables but from where I'm sitting it's nothing but empty promises. Yes, there are offshore wind jobs but they pay 30-40% less than oil and gas, the conditions are worse, and most of the manufacturing is being done overseas. My mates who've tried to transition have either taken massive pay cuts or ended up unemployed. The retraining programmes are a joke - a two-week course doesn't turn a drilling engineer into a wind turbine technician. I'm not against renewables but you can't just throw thousands of skilled workers on the scrapheap and call it progress. Where's the actual plan? Where's the investment in Aberdeen?",
        "source_idx": 2, "location_idx": 21, "author": "u/OffshoreAB",
        "themes": ["Energy and Heating", "Policy and Governance"], "sentiment": -0.65, "classification": "POLICY_DISCUSSION",
        "date_offset_days": -78,
    },
    {
        "title": "Norwich food co-op: local food can fight climate change AND be affordable",
        "content": "I help run a food co-operative in Norwich that sources everything from within 30 miles. We started three years ago with 20 members and we now have over 500. Our weekly veg boxes cost less than the equivalent at Tesco because we cut out the middlemen and the transport costs. We work with 15 local farms who use regenerative practices - no till, cover crops, minimal pesticides. The food is seasonal so you eat what's growing, which takes some adjustment, but honestly the quality is incredible compared to supermarket stuff. We also run cooking classes showing people how to use seasonal produce. The climate impact is significant - our analysis shows our members' food-related emissions are about 40% lower than the national average. Happy to share our model with anyone wanting to set up something similar.",
        "source_idx": 2, "location_idx": 18, "author": "u/NorwichFoodCoop",
        "themes": ["Community Action"], "sentiment": 0.73, "classification": "COMMUNITY_ACTION",
        "date_offset_days": -33,
    },
    {
        "title": "Why is no one talking about the mental health impact of repeated flooding?",
        "content": "I live in York and we've been flooded four times in six years. Each time it's the same cycle: the water comes, you lose everything on the ground floor, you spend months in temporary accommodation, you fight with insurance, you rebuild, and then it happens again. The physical damage is obvious but no one talks about the mental health impact. I have PTSD. I can't sleep when it rains heavily. My children have nightmares about water. Our GP says they're seeing a huge increase in anxiety and depression in flood-affected areas but there's no specific support available. We've become internally displaced people in our own city but because it's 'just' flooding, not a war or earthquake, nobody treats it as the crisis it is. Something has to change.",
        "source_idx": 2, "location_idx": 16, "author": "u/YorkFloodSurvivor",
        "themes": ["Mental Health and Anxiety", "Extreme Weather"], "sentiment": -0.78, "classification": "EMOTIONAL_RESPONSE",
        "date_offset_days": -22,
    },
    {
        "title": "Just installed solar panels in Dundee - here's my 6 month update",
        "content": "Got a 4kW solar panel system installed on our south-facing roof in Dundee six months ago. Here's the honest numbers: April-September generation was much better than I expected for Scotland - averaged about 15kWh per day in summer. We export about 40% back to the grid via SEG at 15p/kWh. Combined with reduced import, our electricity bill has dropped from £120/month to about £45/month. The system cost £6,500 after the Scottish Government grant. At current savings, payback period is about 7 years. Winter generation is obviously much lower - December was about 3kWh per day. But combined with our storage battery (extra £3,000), we're still seeing benefits. Best decision we've made. The installer was local too, so supporting Scottish jobs.",
        "source_idx": 2, "location_idx": 22, "author": "u/DundeeSolarDave",
        "themes": ["Energy and Heating", "Housing and Buildings"], "sentiment": 0.62, "classification": "PRACTICAL_ADAPTATION",
        "date_offset_days": -16,
    },

    # === Additional entries to reach 60+ ===
    {
        "title": "Oxford council's Low Traffic Neighbourhoods causing heated debate",
        "content": "Oxford's controversial Low Traffic Neighbourhood (LTN) schemes continue to divide opinion. Supporters point to reduced through-traffic, safer streets for children, and improved air quality in residential areas. Opponents argue the schemes simply push traffic onto main roads, increase journey times for disabled residents, and have been implemented without adequate consultation. A heated public meeting at the town hall last week saw residents from both sides clash. Council data shows a 30% reduction in traffic on LTN streets but a 15% increase on boundary roads. The debate has become a proxy war for wider disagreements about climate action, personal freedom, and the future of urban transport. Oxford's experience is being closely watched by other cities considering similar measures.",
        "source_idx": 1, "location_idx": 14, "author": "Guardian Transport",
        "themes": ["Cities (Climate Change)", "Policy and Governance", "Community Action"], "sentiment": -0.15, "classification": "POLICY_DISCUSSION",
        "date_offset_days": -58,
    },
    {
        "title": "Rewilding project in the Lake District is transforming the landscape",
        "content": "A major rewilding project in the eastern Lake District is showing remarkable results after just five years. The 1,500-acre site, formerly overgrazed sheep farmland, has seen the return of native woodland, wildflower meadows, and wildlife including red squirrels, barn owls, and for the first time in decades, otters in the local beck. The project, run by a partnership between the National Trust and local landowners, has also reduced downstream flooding by slowing water flow through natural flood management techniques. 'The transformation is extraordinary,' said project manager Helen Frost. 'We're seeing nature recover at a pace we didn't think possible.' Some local farmers remain sceptical, arguing that productive farmland shouldn't be taken out of use. But visitor numbers have increased, creating new economic opportunities for the area.",
        "source_idx": 1, "location_idx": None, "author": "Guardian Country Diary",
        "themes": ["Extreme Weather", "Community Action"], "sentiment": 0.7, "classification": "COMMUNITY_ACTION",
        "date_offset_days": -120,
    },
    {
        "title": "Leicester's textile industry goes green - but at what cost to workers?",
        "content": "Leicester's garment industry, one of the largest in the UK, is being forced to adopt more sustainable practices as major retailers demand lower carbon supply chains. Several factories have invested in energy-efficient machinery and switched to organic fabrics. However, workers and unions warn that the costs are being passed down to an already exploited workforce. 'The factories are cutting wages to pay for their green upgrades,' said one worker who asked not to be named. 'Sustainability should mean sustaining livelihoods too.' The Leicester Garment Workers' Centre reports that working conditions remain poor in many factories despite the green rebranding. The tension highlights a broader question: can climate action succeed if it increases inequality?",
        "source_idx": 1, "location_idx": None, "author": "Guardian Labour",
        "themes": ["Policy and Governance"], "sentiment": -0.4, "classification": "POLICY_DISCUSSION",
        "date_offset_days": -145,
    },
    {
        "title": "My allotment in Sheffield has become my climate therapy",
        "content": "Started my allotment in Sheffield two years ago purely for food growing but it's become something much more important - it's my climate therapy. Being outside, growing food, watching the seasons (however muddled they are now), connecting with other allotment holders - it's the best thing I've ever done for my mental health around climate change. Instead of doom-scrolling about the latest catastrophe, I'm actually doing something tangible. Growing my own food, composting, creating habitat for wildlife. It's small scale but it's real and it matters. Several of us on the site have started sharing climate adaptation tips - what to plant given changing conditions, water-saving techniques, etc. If you're struggling with climate anxiety, I genuinely recommend getting your hands dirty.",
        "source_idx": 4, "location_idx": 5, "author": "u/SheffAllotmentLife",
        "themes": ["Mental Health and Anxiety", "Community Action"], "sentiment": 0.65, "classification": "PRACTICAL_ADAPTATION",
        "date_offset_days": -38,
    },
    {
        "title": "Swansea Bay tidal lagoon rejection was a catastrophic missed opportunity",
        "content": "Three years after the UK Government rejected the Swansea Bay Tidal Lagoon project, it looks like an even bigger missed opportunity than it did at the time. The £1.3 billion project would have generated clean electricity for 155,000 homes for 120 years - yes, 120 years. The technology is proven, the environmental impact was manageable, and it would have created thousands of jobs in South Wales. Instead, the government chose to invest in nuclear at Hinkley Point C, which is now years behind schedule and billions over budget. The tidal lagoon would already be generating power if it had been approved. Welsh politicians continue to campaign for the project to be revived but there's little appetite in Westminster. It's a perfect example of how short-term political thinking undermines long-term climate solutions.",
        "source_idx": 8, "location_idx": 23, "author": "Wales Online Energy",
        "themes": ["Energy and Heating", "Policy and Governance"], "sentiment": -0.55, "classification": "POLICY_DISCUSSION",
        "date_offset_days": -105,
    },
    {
        "title": "As a teacher in London, I see climate anxiety in my students every day",
        "content": "I'm a secondary school teacher in Tower Hamlets and climate anxiety among my students is very real and very present. It comes up in English essays, in science discussions, in PSHE lessons. Some of my Year 10 students have told me they don't see the point in planning for the future because 'the world is ending anyway.' That's heartbreaking to hear from a 15-year-old. We've started a climate action group at school which has helped - giving them agency seems to reduce the anxiety. They've created a school garden, run assemblies on climate topics, and are campaigning for better cycling infrastructure around the school. But the curriculum barely covers climate change in a meaningful way. We need proper climate education that's honest about the challenges but also empowers young people to be part of the solution.",
        "source_idx": 2, "location_idx": 0, "author": "u/TowerHamletsTeacher",
        "themes": ["Mental Health and Anxiety", "Community Action"], "sentiment": -0.32, "classification": "EMOTIONAL_RESPONSE",
        "date_offset_days": -48,
    },
    {
        "title": "Glasgow's green recovery from COP26 - what's actually happened?",
        "content": "Two years after hosting COP26, Glasgow's own green credentials are under scrutiny. The city promised to use the conference as a springboard for local climate action. Some progress has been made: the Clyde riverside development includes Scotland's largest urban park, cycling infrastructure has improved, and several council buildings have been retrofitted. However, air pollution in the city centre remains above legal limits, the promised district heating network is behind schedule, and tree planting targets have been missed. Community groups who were energised by COP26 report feeling let down. 'There was so much energy and optimism,' said climate activist Maria Santos. 'But two years on, the political will seems to have evaporated.' The council argues that progress takes time and that Glasgow remains committed to being net zero by 2030.",
        "source_idx": 7, "location_idx": 8, "author": "The Scotsman Politics",
        "themes": ["Policy and Governance", "Community Action"], "sentiment": -0.28, "classification": "POLICY_DISCUSSION",
        "date_offset_days": -135,
    },
    {
        "title": "We installed a ground source heat pump in rural Norfolk - honest review",
        "content": "We're in a detached 4-bed house in rural Norfolk, off the gas grid, previously heated with oil. Installed a ground source heat pump 18 months ago and here's my honest review. Installation was disruptive - they had to dig up half the garden for the ground loop. Cost £18,000 with the BUS grant covering £6,000. The system works brilliantly from March to November - the house is evenly heated and our bills are about 60% of what we paid for oil. However, in the coldest weeks of winter (below -5°C), it struggles and we've supplemented with electric radiators in the bedrooms. The system also required us to upgrade all radiators to larger ones as heat pumps run at lower temperatures. Overall I'd recommend it but go in with realistic expectations. It's not a like-for-like replacement for a gas boiler.",
        "source_idx": 2, "location_idx": 18, "author": "u/NorfolkRuralLife",
        "themes": ["Energy and Heating", "Housing and Buildings"], "sentiment": 0.28, "classification": "PRACTICAL_ADAPTATION",
        "date_offset_days": -52,
    },
    {
        "title": "Climate protest blocks Edinburgh Royal Mile - tourists furious, locals divided",
        "content": "Climate activists from Extinction Rebellion blocked the Royal Mile in Edinburgh for six hours yesterday, disrupting tourist access to Edinburgh Castle and causing traffic chaos across the Old Town. The protesters demanded the Scottish Government declare a 'genuine climate emergency' and ban all new fossil fuel projects. Reaction was sharply divided. Tourists were frustrated, with some having paid for pre-booked castle tours they couldn't reach. Local businesses reported lost trade. But many Edinburgh residents expressed support. 'Tourism won't exist if we don't have a habitable planet,' said one onlooker. Police Scotland made 23 arrests. The protest coincided with the release of new data showing Scotland's emissions reduction targets are at risk of being missed.",
        "source_idx": 7, "location_idx": 7, "author": "The Scotsman News",
        "themes": ["Community Action", "Policy and Governance"], "sentiment": -0.25, "classification": "COMMUNITY_ACTION",
        "date_offset_days": -88,
    },
    {
        "title": "Flooding has destroyed my business. Insurance won't cover it anymore.",
        "content": "I run a small antiques shop on the ground floor of a building in central York. We've flooded five times in eight years. After the third flood, our insurer dropped us. After the fourth, no insurer would touch us at any price. The fifth flood last month destroyed £80,000 of stock. I'm facing bankruptcy. The council talks about flood defences but nothing gets built. The government offers emergency grants that cover a fraction of the damage. I've put my life into this business and climate change is literally washing it away. I know I'm not alone - there are businesses along the Ouse that have just given up. The high street is dying and flooding is accelerating it. What are we supposed to do? Where are we supposed to go?",
        "source_idx": 2, "location_idx": 16, "author": "u/YorkAntiquesShop",
        "themes": ["Extreme Weather"], "sentiment": -0.82, "classification": "EMOTIONAL_RESPONSE",
        "date_offset_days": -10,
    },
    {
        "title": "Cambridge start-up develops AI tool to predict UK flood risk street-by-street",
        "content": "A Cambridge-based start-up has developed an AI system that can predict flood risk for individual streets across the UK, using a combination of satellite data, historical flood records, local drainage information, and climate projections. The tool, called FloodSight, provides risk assessments for 2030, 2040, and 2050 under different climate scenarios. Early users include local councils, insurance companies, and property developers. 'Traditional flood maps are too coarse and too static,' said founder Dr Priya Sharma. 'Our system updates in near real-time and can predict flood risk down to individual property level.' The company has raised £5 million in seed funding and is working with the Environment Agency to validate its predictions against real-world events. The tool is also being made available free to individual homeowners checking their property risk.",
        "source_idx": 1, "location_idx": 15, "author": "Guardian Technology",
        "themes": ["Extreme Weather"], "sentiment": 0.52, "classification": "PRACTICAL_ADAPTATION",
        "date_offset_days": -72,
    },
    {
        "title": "Is it just me or is anyone else angry about greenwashing?",
        "content": "Every company now claims to be 'sustainable' or 'carbon neutral' or 'eco-friendly' and most of it is complete rubbish. My local supermarket has 'sustainably sourced' labels on products flown in from the other side of the world. My energy company sends emails about their 'green commitment' while reporting record profits. Airlines offer to 'offset' your flight for £2 as if planting a tree in Guatemala cancels out burning jet fuel. Banks that fund fossil fuel projects have 'net zero pledges.' It's infuriating. Genuine climate action is being undermined by this tsunami of greenwash because it makes consumers cynical and confused. The ASA needs much stricter rules on environmental claims. If a product isn't genuinely low-carbon, you shouldn't be able to market it as green. Rant over.",
        "source_idx": 3, "location_idx": None, "author": "u/GreenwashDetector",
        "themes": ["Policy and Governance"], "sentiment": -0.58, "classification": "EMOTIONAL_RESPONSE",
        "date_offset_days": -5,
    },
    {
        "title": "How our street in Manchester became a climate-friendly community",
        "content": "Three years ago, a few of us on our street in Chorlton decided to work together on climate action. We started with a WhatsApp group and now we've achieved: a community tool library (so no one buys a drill they use twice), a street composting scheme, a car-sharing pool that's taken four cars off the road, a bulk-buying co-op for organic food, seasonal street parties using surplus food, and we've collectively insulated 15 houses using a group discount from a local installer. The total investment has been minimal - mostly time and goodwill. The street feels completely different now. People know each other, help each other, and we've probably reduced our collective carbon footprint by 20-30%. The social benefits are honestly even bigger than the environmental ones. Starting point: just knock on your neighbours' doors.",
        "source_idx": 2, "location_idx": 1, "author": "u/ChorltonGreenStreet",
        "themes": ["Community Action", "Housing and Buildings"], "sentiment": 0.8, "classification": "COMMUNITY_ACTION",
        "date_offset_days": -27,
    },
    {
        "title": "Cornwall tourism industry braces for impact of coastal erosion",
        "content": "Cornwall's tourism industry, worth over £3 billion annually, is facing an existential threat from accelerating coastal erosion driven by rising sea levels and more frequent storms. Several iconic beaches have lost significant sand, cliff-top paths have been rerouted, and some coastal properties have been declared unsafe. The Minack Theatre, one of Cornwall's most popular attractions, has invested £2 million in coastal protection works. Holiday park operators near cliff edges are facing difficult decisions about relocation. Cornwall Council has published a Shoreline Management Plan that effectively acknowledges some areas cannot be defended and will need to be abandoned to the sea. 'This is the reality of climate change on our doorstep,' said coastal geologist Dr Emma Wilson. 'We need honest conversations about managed retreat.'",
        "source_idx": 1, "location_idx": None, "author": "Guardian Travel",
        "themes": ["Extreme Weather"], "sentiment": -0.5, "classification": "PRACTICAL_ADAPTATION",
        "date_offset_days": -155,
    },
    {
        "title": "Belfast community garden bringing together divided communities through growing",
        "content": "A community garden project on the peace line between the Falls and Shankill Roads in Belfast is using food growing to bring together communities that have been divided for decades. The Garden of Reconciliation, established two years ago on wasteland beside a peace wall, now has over 80 members from both nationalist and unionist backgrounds. 'When you're elbow-deep in compost, nobody cares about your politics or religion,' said coordinator Siobhan Kelly. The garden produces vegetables for a weekly community meal that regularly attracts over 100 people. It has also become a space for climate education workshops and has recently installed a small community solar array. 'Climate change doesn't care about borders or identity,' said one participant. 'If anything can unite us, dealing with this crisis together can.'",
        "source_idx": 0, "location_idx": 10, "author": "BBC News Northern Ireland",
        "themes": ["Community Action"], "sentiment": 0.75, "classification": "COMMUNITY_ACTION",
        "date_offset_days": -82,
    },
    {
        "title": "UK heat pump installations finally accelerating but still behind target",
        "content": "Heat pump installations in the UK reached 55,000 in the first quarter of 2024, a significant increase from 35,000 in the same period last year, but still well below the government's target of 600,000 per year by 2028. The increase is attributed to improved grant schemes, falling prices due to economies of scale, and growing consumer awareness. However, significant barriers remain: the upfront cost averaging £10,000-£15,000 even after grants, a shortage of qualified installers, and concerns about performance in poorly insulated homes. Industry body the Heat Pump Association says the supply chain is ready to scale but needs consistent policy support. 'Stop-start policy kills investment,' said HPA chair Sarah Mitchell. 'We need a clear, long-term signal that heat pumps are the future of UK heating.'",
        "source_idx": 0, "location_idx": None, "author": "BBC News Business",
        "themes": ["Energy and Heating", "Housing and Buildings", "Policy and Governance"], "sentiment": 0.15, "classification": "POLICY_DISCUSSION",
        "date_offset_days": -3,
    },
    {
        "title": "Living next to a wind farm in rural Wales - the reality",
        "content": "We've lived about 800 metres from a wind farm in mid-Wales for three years now. The reality is much less dramatic than either side of the debate suggests. Can we hear them? Yes, sometimes, when the wind is from a certain direction. It's a low whooshing sound. Annoying? Occasionally. Unbearable? Absolutely not. We hear the main road more. The visual impact is real but you get used to it, and there's something quite elegant about them against the hills. The community benefit fund has paid for a new playground, contributed to the village hall renovation, and funds bursaries for local young people. Our property value hasn't noticeably changed. Overall, I'd much rather live near a wind farm than a coal plant, a fracking site, or face the consequences of doing nothing about climate change. The hysteria about wind farms is wildly overblown.",
        "source_idx": 2, "location_idx": None, "author": "u/MidWalesLife",
        "themes": ["Energy and Heating", "Community Action"], "sentiment": 0.38, "classification": "PRACTICAL_ADAPTATION",
        "date_offset_days": -67,
    },
    {
        "title": "UK biodiversity crisis: one in six species at risk of extinction",
        "content": "A landmark report by the Natural History Museum and conservation charities reveals that one in six species in the UK is now at risk of extinction. The State of Nature 2024 report, compiled by over 100 organisations, documents a 19% decline in average species abundance since systematic monitoring began in 1970. Farmland birds have declined by 60%, pollinating insects by 30%, and freshwater species by 22%. Climate change is identified as an increasingly significant driver alongside habitat loss and pollution. The report highlights that while some flagship species like otters and red kites have recovered through targeted conservation, the broader picture is of continued decline. The authors call for legally binding nature recovery targets, major reform of agricultural subsidies, and the protection of 30% of UK land and sea by 2030.",
        "source_idx": 1, "location_idx": None, "author": "Guardian Environment",
        "themes": ["Policy and Governance"], "sentiment": -0.55, "classification": "POLICY_DISCUSSION",
        "date_offset_days": -115,
    },
    {
        "title": "Trying to go car-free in Newcastle - is it even possible?",
        "content": "My partner and I decided to go car-free in Newcastle three months ago after calculating our car was costing us £4,000 a year including finance, insurance, parking, and fuel. The verdict: it's mostly possible but with significant frustrations. The Metro is decent for getting around Tyneside. The bus network is okay but unreliable - we've missed appointments because buses just didn't turn up. Cycling infrastructure is patchy - some good routes exist but there are dangerous gaps. Getting to the coast or countryside without a car is genuinely difficult. We've joined a car club for occasional needs which works well. Grocery delivery has replaced the weekly big shop. Overall we're saving about £3,000 a year and are fitter from cycling. But I understand why most people haven't made the switch - the infrastructure just isn't there yet outside London.",
        "source_idx": 2, "location_idx": 11, "author": "u/NewcastleNoCar",
        "themes": ["Cities (Climate Change)"], "sentiment": 0.2, "classification": "PRACTICAL_ADAPTATION",
        "date_offset_days": -14,
    },
    {
        "title": "Climate change is already affecting house prices across the UK",
        "content": "New analysis by property data firm HomeTrack reveals that climate risks are already being priced into UK house prices. Properties in areas with high flood risk are selling for an average of 7% less than comparable properties in lower-risk areas, up from 3% five years ago. Coastal properties in areas identified as vulnerable to erosion are seeing even larger discounts. Conversely, energy-efficient homes with high EPC ratings are commanding premiums of 5-10%. The trend is expected to accelerate as climate risks become more apparent and as mortgage lenders increasingly factor environmental risk into their assessments. 'Climate change is the biggest emerging risk to UK property values,' said HomeTrack director James Fergusson. 'Buyers and investors who ignore it do so at their financial peril.'",
        "source_idx": 1, "location_idx": None, "author": "Guardian Property",
        "themes": ["Housing and Buildings", "Extreme Weather"], "sentiment": -0.35, "classification": "PRACTICAL_ADAPTATION",
        "date_offset_days": -7,
    },
]


async def seed_database(db_session):
    """Seed the database with test data."""
    from app.models.models import (
        Source, Location, Theme, DiscourseSample, SentimentAnalysis,
        DiscourseClassification, ResearchNote, User, sample_themes,
        SourceType, Region, SentimentLabel, ClassificationType
    )
    from app.core.security import get_password_hash
    from datetime import datetime, timezone
    import uuid

    print("Seeding database...")

    # Create test user
    test_user = User(
        id=str(uuid.uuid4()),
        email="researcher@thermoculture.ac.uk",
        hashed_password=get_password_hash("research2024"),
        full_name="Dr. Sarah Thompson",
        is_active=True,
    )
    db_session.add(test_user)
    await db_session.flush()
    print(f"Created test user: {test_user.email}")

    # Create locations
    location_records = []
    for loc_data in LOCATIONS:
        loc = Location(
            id=str(uuid.uuid4()),
            name=loc_data["name"],
            region=Region[loc_data["region"]],
            latitude=loc_data["latitude"],
            longitude=loc_data["longitude"],
        )
        db_session.add(loc)
        location_records.append(loc)
    await db_session.flush()
    print(f"Created {len(location_records)} locations")

    # Create sources
    source_records = []
    for src_data in SOURCES:
        src = Source(
            id=str(uuid.uuid4()),
            name=src_data["name"],
            source_type=SourceType[src_data["source_type"]],
            url=src_data["url"],
            description=src_data["description"],
            is_active=True,
        )
        db_session.add(src)
        source_records.append(src)
    await db_session.flush()
    print(f"Created {len(source_records)} sources")

    # Create themes
    theme_records = {}
    for theme_data in THEMES:
        theme = Theme(
            id=str(uuid.uuid4()),
            name=theme_data["name"],
            description=theme_data["description"],
            category=theme_data["category"],
        )
        db_session.add(theme)
        theme_records[theme_data["name"]] = theme
    await db_session.flush()
    print(f"Created {len(theme_records)} themes")

    # Create discourse samples with analysis
    base_date = datetime(2024, 6, 15, tzinfo=timezone.utc)
    sample_count = 0

    for sample_data in DISCOURSE_SAMPLES:
        sample_date = base_date + timedelta(days=sample_data["date_offset_days"])

        location_id = None
        if sample_data.get("location_idx") is not None:
            location_id = location_records[sample_data["location_idx"]].id

        sample = DiscourseSample(
            id=str(uuid.uuid4()),
            title=sample_data["title"],
            content=sample_data["content"],
            source_id=source_records[sample_data["source_idx"]].id,
            source_url=None,
            author=sample_data.get("author"),
            published_at=sample_date,
            collected_at=sample_date + timedelta(hours=randint(1, 48)),
            location_id=location_id,
            raw_metadata={"seed_data": True},
        )
        db_session.add(sample)
        await db_session.flush()

        # Link themes
        for theme_name in sample_data.get("themes", []):
            if theme_name in theme_records:
                await db_session.execute(
                    sample_themes.insert().values(
                        sample_id=sample.id,
                        theme_id=theme_records[theme_name].id,
                    )
                )

        # Create sentiment analysis
        sentiment_score = sample_data.get("sentiment", 0.0)
        if sentiment_score < -0.6:
            label = SentimentLabel.VERY_NEGATIVE
        elif sentiment_score < -0.2:
            label = SentimentLabel.NEGATIVE
        elif sentiment_score < 0.2:
            label = SentimentLabel.NEUTRAL
        elif sentiment_score < 0.6:
            label = SentimentLabel.POSITIVE
        else:
            label = SentimentLabel.VERY_POSITIVE

        sentiment = SentimentAnalysis(
            id=str(uuid.uuid4()),
            sample_id=sample.id,
            overall_sentiment=sentiment_score,
            sentiment_label=label,
            confidence=uniform(0.7, 0.95),
            analyzed_at=sample.collected_at + timedelta(minutes=randint(1, 30)),
        )
        db_session.add(sentiment)

        # Create discourse classification
        classification = DiscourseClassification(
            id=str(uuid.uuid4()),
            sample_id=sample.id,
            classification_type=ClassificationType[sample_data.get("classification", "PRACTICAL_ADAPTATION")],
            confidence=uniform(0.65, 0.95),
            classified_at=sample.collected_at + timedelta(minutes=randint(1, 30)),
        )
        db_session.add(classification)

        sample_count += 1

    await db_session.flush()
    print(f"Created {sample_count} discourse samples with analysis")

    # Create sample research notes
    notes = [
        {
            "title": "Initial observations on UK climate discourse patterns",
            "content": """# Initial Observations on UK Climate Discourse Patterns

## Key Findings

1. **Geographic variation**: Climate discourse varies significantly by region. Scotland focuses more on energy transition and renewable success stories, while South East England discourse centres on water scarcity and housing.

2. **Emotional responses are prevalent**: A significant portion of discourse, particularly on social media, involves emotional responses including anxiety, frustration, and grief. This suggests thermoculture involves deep affective engagement, not just practical concerns.

3. **Practical adaptation is the most common discourse type**: People are most likely to discuss climate change in terms of practical changes they're making or considering - heat pumps, insulation, transport changes, food growing.

4. **Policy frustration cuts across political lines**: Both left and right-leaning discourse expresses frustration with government climate policy, though for different reasons.

## Next Steps
- Analyse temporal patterns more closely
- Map the relationship between extreme weather events and discourse spikes
- Investigate the community action category further
""",
        },
        {
            "title": "Thermoculture and lived experience: preliminary framework",
            "content": """# Thermoculture and Lived Experience: Preliminary Framework

## Working Definition

Thermoculture encompasses the cultural, emotional, practical, and political dimensions of how UK communities experience and respond to climate change in their daily lives.

## Proposed Analytical Framework

### 1. Material Thermoculture
- Physical adaptations to homes and buildings
- Changes in food production and consumption
- Transport behaviour changes
- Water usage adaptation

### 2. Affective Thermoculture
- Eco-anxiety and climate grief
- Hope and agency through action
- Intergenerational tension
- Seasonal disorientation

### 3. Political Thermoculture
- Policy engagement and frustration
- Community organising and protest
- Denial and resistance
- Just transition debates

### 4. Social Thermoculture
- Community resilience building
- Neighbourhood-level action
- Knowledge sharing and mutual aid
- Identity and belonging through climate action

## Methodological Notes
- Mixed methods approach combining quantitative NLP analysis with qualitative close reading
- Geographic and temporal analysis essential
- Need to capture voices often excluded from mainstream discourse
""",
        },
    ]

    for note_data in notes:
        note = ResearchNote(
            id=str(uuid.uuid4()),
            title=note_data["title"],
            content=note_data["content"],
            user_id=test_user.id,
        )
        db_session.add(note)

    await db_session.commit()
    print("Seed data complete!")
    print(f"Summary: 1 user, {len(location_records)} locations, {len(source_records)} sources, "
          f"{len(theme_records)} themes, {sample_count} discourse samples, {len(notes)} research notes")


if __name__ == "__main__":
    print("This module should be run via the seed command: python -m seeds.run_seed")
