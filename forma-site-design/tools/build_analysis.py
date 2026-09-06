# -*- coding: utf-8 -*-
import json

C = [
 ("forma","Autodesk Forma Site Design","autodesk.com",0,"anchor (user-supplied URL)",
  "early-phase site design and analysis","AEC firms, mid-to-large","US (Autodesk, San Francisco)",
  "Data-driven software for site design and analysis, part of the early-phase tools for Forma",
  "Sells the early phase as a place where environmental performance is decided, not just geometry: wind, sun, daylight, carbon read in seconds, then handed to Revit.",
  "Architects and designers inside the Autodesk estate; the blog's own words are 'architects and designers'",
  "per-seat subscription, published; also bundled in the AEC Collection","approx. $185/mo or $1,445/yr standalone (third-party reported; page unreadable)",
  ["Designing with wind: what a children's science museum taught us",
   "Schematic design in multifamily projects: when decisions-and mistakes-scale",
   "How does Forma Site Design work with Revit and other tools?"]),

 ("testfit","TestFit","testfit.io",1,"search: 'Spacemaker alternatives'; named repeatedly against Forma",
  "real estate feasibility","developer deal teams, US","US (Dallas)",
  "Real Estate Feasibility Platform","Puts the deal, not the drawing, at the centre: site plans exist to serve a pro forma.",
  "'Built for the Deal Team' - developers, architects and contractors","per-seat published tiers, free tier","$0/mo entry; $200-$300 tiers; $10,000 figure on pricing",
  ["Automate Site Plans. Accelerate Decisions.","A New Real Estate Feasibility Workflow","Minimize Earthwork Cost with Automatic Cut and Fill"]),

 ("giraffe","Giraffe","giraffe.build",1,"search: 'Autodesk Forma alternatives'",
  "real estate decision platform","developers, planners, local government","Australia (Sydney)",
  "The Orchestration Layer for AI-Driven Real Estate","Reframes the category away from a design tool and towards an enterprise decision system that absorbs the consultants.",
  "'developers, planners, designers, and analysts who want to move fast'; also 'For Local Governments & Municipalities'","contact sales","no published figure; 'no credit card' trial",
  ["Build beautiful cities","Giraffe integrates fragmented workflows into a single structured decision system.","AI is changing the economics of doing real estate."]),

 ("snaptrude","Snaptrude","snaptrude.com",1,"search: 'conceptual design software wind noise daylight'",
  "AI BIM for architects","architecture practices","India / US",
  "The AI-Powered BIM software for Architects","The one competitor that promises the whole arc - brief to BIM - in a single model, rather than handing off at concept.",
  "Architects; 'Driven by Architects Powered by AI'","per-seat published, free tier","$0; $60/month; $100/month",
  ["From brief to BIM, in one connected model","10 AI agents for zoning, site analysis, massing, floor plans & more","Concept to BIM-ready models in your browser"]),

 ("dbf","Digital Blue Foam","digitalbluefoam.com",1,"search: 'generative site planning massing feasibility'",
  "spatial reasoning AI","cities, governments, asset owners","Singapore",
  "Your spatial reasoning layer for every asset decision.","Has climbed out of the design-tool category entirely into an AI reasoning layer sold to institutions.",
  "'cities, governments and asset owners'","contact sales","talk to sales only",
  ["One engine, every spatial decision","Ask a real spatial question Get a defensible answer","Anyone can call an LLM The spatial memory beneath it is the moat"]),

 ("hypar","Hypar","hypar.io",1,"search: 'early stage design platform comparison'",
  "space planning","architecture firms","US",
  "Space planning software for building buy-in","Narrowest promise in the level-1 set, and the most explicit about the human problem: agreement, not optimisation.",
  "Project teams and their clients; 'Studio tier for firms standardizing on Hypar'","per-seat published","$100 per user per month",
  ["Hypar is space planning software for building buy-in: early-phase architectural space planning in the browser.",
   "Plan buildings your client and team can agree on faster.","Import site and Revit data, edit with automatic measurement, export to Revit."]),

 ("finch","Finch","finch3d.com",1,"search: 'comparing early-stage feasibility tools 2026'",
  "AI-native building design","AEC professionals, Europe","Sweden (Stockholm)",
  "AI for how the world builds","Sells breadth of exploration - thousands of options with live trade-off data - rather than a finished answer.",
  "'Built by architects, for the way AEC professionals actually design and make decisions.'","published tiers","EUR 79 entry; EUR 14,500 upper tier",
  ["AI-native platform for building design","Test thousands of design options to understand trade-offs with real-time data","Encode design systems"]),

 ("bentley","Bentley OpenSite+","bentley.com",1,"search: 'site design software' - direct name-match competitor",
  "civil site design","civil engineers, land development","US (Exton, PA)",
  "OpenSite+: AI-Powered Site Design Software","Owns the literal phrase 'site design software' from the civil-engineering end, where the deliverable is grading and construction documents.",
  "Engineers and drafters on commercial, industrial and residential sites","enterprise / quote","no accessible pricing",
  ["OpenSite+: AI-Powered Site Design Software","The First AI-driven Civil Engineering Software for Site Design","Civil WorkSuite: Site Design Software"]),

 ("archistar","Archistar","archistar.ai",1,"search: 'Giraffe competitors'",
  "AI plan review and permitting","local governments","Australia (Sydney)",
  "Fast-track building permits with AI plan review","Started in site feasibility and has repositioned onto the regulator's side of the table - permitting, not proposing.",
  "'local governments'; 'Trusted by Los Angeles and Austin'","published tiers","$95, $345/mo, $595",
  ["AI PreCheck is trusted by 30-plus cities and local governments worldwide",
   "Trusted by Los Angeles and Austin to cut permit approval times by up to 55%","Standardized assessment in minutes"]),

 ("architechtures","Architechtures","architechtures.com",2,"search: 'generative residential buildings'",
  "AI building generator","residential architects","Spain (Madrid)",
  "AI-Powered Building Design","Generation speed is the whole pitch; site context barely features.",
  "Architects doing residential buildings","published tiers","$49 / $294 / $588 / $3,528",
  ["AI Architecture Generator in Real-Time","Generate optimal building designs in real-time","Reduces architectural design time"]),

 ("maket","Maket","maket.ai",2,"search: 'TestFit alternatives'",
  "AI home design","homeowners and small practices","Canada",
  "The AI Home Design Studio","The consumer end of the category - 'Anyone can design a home' is the opposite of a professional site tool.",
  "'Anyone can design a home'","freemium published","$0 / $20 / $100 per month",
  ["The future of home design","Anyone can design a home","generate floor plans, edit by chat, and visualize your space in minutes"]),

 ("zenerate","Zenerate","zenerate.ai",2,"search: 'TestFit alternatives'",
  "AI feasibility studies","land developers","US",
  "AI Feasibility Study Tool for Land Development","Same wedge as TestFit, narrower: feasibility studies delivered as an output, in minutes.",
  "Land development teams; built by 'architects, AI developers, designers, computational designers'","subscription, figures not published","free trial; 'Subscription Plans' with no figures",
  ["AI-Powered Feasibility Studies Delivered in Minutes",
   "Instantly generate optimized site plans, floor plans, and parking layouts with pro forma insights for faster land development.","Ready to See It on Your Own Site?"]),

 ("arkdesign","ArkDesign.AI","arkdesign.ai",2,"search: 'TestFit alternatives'",
  "AI feasibility for multifamily","architects and developers, multifamily","US",
  "AI-Powered Design & Feasibility Studies for Multi-Family & Mixed-Use Projects","Leads with the developer's outcome in three words and never softens it.",
  "'A tool for architects and real estate developers'","not published","no pricing page found",
  ["Generate More Profit","Up to code","How industry leaders are using ARK"]),

 ("deepblocks","Deepblocks","deepblocks.com",2,"search: 'site feasibility land development software'",
  "AI site selection and feasibility","real estate developers, US cities","US (Miami)",
  "AI-driven site selection and feasibility","The most financially explicit site in the corpus: real deals, real return percentages, on the homepage.",
  "Developers and underwriters","published tiers","$55.55/mo; $499/mo; $1,999/mo; $3,999/mo",
  ["...yielding an 8.44% return on cost.","...a variance scenario reaching a 42% return on cost.",
   "connect the feasibility study to your existing pro forma"]),

 ("landtech","LandTech","land.tech",2,"search: 'site feasibility land development software'",
  "land sourcing and appraisal","UK land and development teams","UK (London)",
  "Faster & Smarter Land Decisions for Developers","Owns the step before design entirely - find the land, prove it works, then someone else draws it.",
  "'Built for every type of land professional'; 'UK developers'","published","GBP 150 / month",
  ["All Your Land Decisions, Powered by One Intelligent Platform.","An ecosystem built for the full development journey.",
   "Identify high-demand locations and build profitable, compliant schemes with confidence"]),

 ("modelur","Modelur (AgiliCity)","modelur.com",2,"search: 'urban planning platform competitors'",
  "early-stage urban design","architects and urban designers","Slovenia",
  "Fast and Accurate 3D Massing and Feasibility Studies","Positions as a plugin, not a platform: 'SketchUp Supercharged'.",
  "Architects doing urban massing","published per-seat, free tier","EUR 0 / EUR 74 per seat / EUR 149 per seat",
  ["SketchUp Supercharged","Better Early Stage Decisions and Super-Fast Iterations","calculates key urban parameters in real-time"]),

 ("hektar","Hektar","hektar.ai",2,"search: 'Spacemaker alternatives'",
  "volume studies and site feasibility","Nordic developers, architects, municipalities","Sweden",
  "Volume Studies & Site Feasibility in Minutes","Regionally anchored and openly so - the Nordics are named in the meta description.",
  "'developers, architects, and municipalities across the Nordics'","contact sales","talk to sales",
  ["Explore your site. Volume studies in minutes.","Hektar generates volume studies, density scenarios and KPIs for raw land in minutes.",
   "A Number Without Context Is Just a Number"]),

 ("cove","cove.tool (cove.inc)","cove.inc",2,"adjacent: early-stage building performance analysis",
  "building performance analysis","architects and engineers","US (Atlanta)",
  "No copy available - site returns an HTTP 202 bot challenge","Not plotted: no first-party copy could be read, so any position would be invented.",
  "unknown from copy","unknown","unknown", []),

 ("esri","Esri ArcGIS Urban","esri.com",2,"adjacent: urban planning / GIS incumbent",
  "urban planning and design","cities and planning departments","US (Redlands)",
  "Urban Planning, Design & Development Software","The GIS incumbent: context data is the product, design is a feature on top of it.",
  "Cities; planners and development review teams","enterprise / quote","free trial only",
  ["Transforming urban planning and design","3D scenario modeling","Project e-submission"]),

 ("urbansim","UrbanSim","urbansim.com",2,"search: 'Giraffe competitors'",
  "urban simulation","cities and regional agencies","US (Berkeley)",
  "Smarter Urban Development with AI","Simulation and forecasting for public agencies, a scale above any single site.",
  "'cities and developers'","not published","no pricing page",
  ["PLAN DIFFERENTLY","PLAN INTELLIGENTLY","helps cities and developers to build smarter and more sustainable cities, and reduce costs"]),

 ("sketchup","SketchUp (Trimble)","sketchup.com",2,"adjacent incumbent: named top alternative on directories",
  "3D design","architects, designers, builders","US (Trimble)",
  "Bring your vision to life","The general-purpose modeller these tools are measured against, and the substrate Modelur plugs into.",
  "'architects, designers, and builders'","published per-seat","$10.75 / $30 / $33.25 / $40",
  ["Design in 3D, from concept to construction","Revolutionize the way you create","Connected tools. Seamless workflow."]),

 ("vectorworks","Vectorworks Landmark","vectorworks.net",2,"adjacent: landscape/site design incumbent",
  "landscape design","landscape architects","US (Columbia, MD)",
  "THE ULTIMATE LANDSCAPE DESIGN SOFTWARE","The other reading of 'site design': planting, irrigation and documentation, all the way to drawings.",
  "Landscape architects","perpetual/subscription, quote","free trial; 'Buy Now'",
  ["Landscape design software for every project phase","Work Smarter with 3D Landscape BIM Software",
   "transform your design, presentation, irrigation, and documentation workflows"]),

 ("aprao","Aprao","aprao.com",2,"search: 'development site finder software'",
  "development appraisal","property developers and lenders","UK (London)",
  "Assess every real estate deal with confidence","Pure finance: no geometry at all, which makes it the clean money-end pole of this market.",
  "Developers, valuers and lenders","subscription, figures not published","free trial; no figures on pricing page",
  ["The financial-modelling engine for the AI era","Everything you need to run your numbers with confidence","Enterprise-grade security, by default"]),

 ("landchecker","Landchecker","landchecker.com.au",2,"search: 'development site finder software'",
  "property and land data","Australian property professionals","Australia (Melbourne)",
  "Australian property data in one place - for faster, insight-driven decisions","Data utility, single country, priced like a subscription service rather than a design tool.",
  "'thousands of businesses'; Australian property professionals","published tiers","$0 / $200 / $240 / $2,400 per year",
  ["The complete property intelligence platform","Planning Zones, Overlays and Layers","Permits and Development Applications"]),

 ("urbanfootprint","UrbanFootprint","urbanfootprint.com",2,"adjacent: urban/land-use analytics",
  "resilience decision intelligence","utilities, government, finance","US (Berkeley)",
  "The Resilient Decision Intelligence Platform","Has left design behind for risk and climate analytics sold to institutions.",
  "Utilities, public agencies and financial institutions","enterprise / quote","pricing page with no figures",
  ["Resilience Insights for where to","Climate Risk & Sustainability","Assess risk and make data-driven decisions"]),

 ("geopogo","Geopogo","geopogo.com",2,"search: 'Giraffe competitors'",
  "AI for architecture","architects using Revit","US",
  "AI for Architecture: Claude to Revit & 3D City Models","Sells the connective tissue - AI into Revit, and city context out - rather than a design environment.",
  "Architects working in Revit, Unreal, Blender, SketchUp","not readable","site renders client-side; no pricing readable",
  ["Design and edit Revit models with Claude AI - and download real-world 3D city models in seconds."]),

 ("skema","Skema","skema.ai",2,"adjacent: precedent-driven early design",
  "generative design for AEC","architects and engineers","US",
  "Generative Design for AEC","Argues from the handoff problem: the value is carrying design intent into BIM, not generating options.",
  "Architects and engineers","published tiers","$199 / month; $750 / month",
  ["Design Intent Doesn't Survive the Handoff","Put Your Proven Designs Back to Work !","Your New BIM Workflow"]),

 ("civilsai","Civils.ai","civils.ai",2,"adjacent: AI for civil/site engineering",
  "AI quantity takeoff","groundworks contractors","Singapore / UK",
  "AI Quantity Takeoffs & Checks for Contractors","Downstream of everyone else: the site after it has been designed, priced for the contractor.",
  "'groundworks contractors'","published tiers","$90 / month; $270 / month",
  ["Accurate AI Takeoffs & Checks before your project breaks ground.","Cut takeoff time by up to 90%","Estimate your ROI in seconds."]),

 ("transoft","Transoft Solutions","transoftsolutions.com",2,"adjacent: civil site design tooling",
  "transportation design software","transportation professionals","Canada (Vancouver)",
  "Innovative Solutions for Transportation Professionals","Adjacent discipline - movement and safety on the site rather than what gets built on it.",
  "'transportation professionals'","quote","no pricing page",
  ["Empowering Transportation Professionals Since 1991","help professionals plan, design, and operate safe transportation systems"]),

 ("rhino","Rhino (McNeel)","rhino3d.com",2,"adjacent incumbent: Grasshopper is the parametric baseline these tools displace",
  "3D modelling","designers and computational designers","US (Seattle)",
  "Rhino - Design, Model, Present, Analyze, Realize","The open modelling substrate; every generative claim in this market is implicitly a claim against a Grasshopper script.",
  "Designers and computational designers","perpetual licence","no price captured in scan",
  ["Rhino 8","Design, Model, Present, Analyze, Realize..."]),
]

companies = [dict(zip(
  ["id","name","domain","level","discovered_via","category","segment","hq","one_liner",
   "positioning","icp","pricing_model","price_signal","key_claims"], c)) for c in C]
for c in companies:
    c["parent"] = "" if c["level"] == 0 else "autodesk.com"

E = {}  # evidence bank, per matrix below
print(json.dumps({"companies": len(companies)}))
with open('/tmp/claude-0/-home-user-desk-research-/dde76782-afb8-5844-9f8f-b0df56abe4a2/scratchpad/companies.json','w') as f:
    json.dump(companies, f, indent=1, ensure_ascii=False)
