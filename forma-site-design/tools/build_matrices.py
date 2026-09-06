# -*- coding: utf-8 -*-
import json, datetime, pathlib
S = pathlib.Path('/tmp/claude-0/-home-user-desk-research-/dde76782-afb8-5844-9f8f-b0df56abe4a2/scratchpad')
companies = json.load(open(S/'companies.json'))

def M(mid, title, why, xl, xlo, xhi, yl, ylo, yhi, quad, pts, reading):
    return {"id": mid, "title": title, "why_it_matters": why,
            "x": {"label": xl, "low": xlo, "high": xhi},
            "y": {"label": yl, "low": ylo, "high": yhi},
            "quadrants": quad,
            "points": [{"company": c, "x": x, "y": y, "evidence": e} for c, x, y, e in pts],
            "reading": reading}

matrices = []

# ---------------------------------------------------------------- 1 positioning
matrices.append(M(
 "wedge", "The wedge: what the early decision is for",
 "Everyone here shortens the same phase. They disagree about what that phase is deciding - how the building performs, or whether the deal works.",
 "What the early study optimises", "environmental and design performance", "financial return on the deal",
 "Scope of the promise", "one early study", "end-to-end decision platform",
 {"tl": "Design platforms", "tr": "Deal operating systems",
  "bl": "Performance point tools", "br": "Feasibility calculators"},
 [
  ("forma",1.5,5.0,"H2 on blogs.autodesk.com/forma: 'Designing with wind: what a children's science museum taught us'; also 'Total Carbon Analysis in Forma Building Design'"),
  ("testfit",8.0,6.0,"meta on testfit.io: 'Optimize for the best site layout instantly with TestFit's site planning AI to meet both your pro forma and design intent.'"),
  ("giraffe",7.0,9.5,"H2 on giraffe.build: 'AI is changing the economics of doing real estate.'; title: 'The Orchestration Layer for AI-Driven Real Estate'"),
  ("snaptrude",2.5,7.0,"H1 on snaptrude.com: 'From brief to BIM, in one connected model'"),
  ("dbf",5.5,8.0,"meta on digitalbluefoam.com: 'ranked spatial scenarios scored on spatial ROI, infrastructure and liveability'"),
  ("hypar",2.0,3.0,"hypar.io/llms.txt: 'space planning software for building buy-in: early-phase architectural space planning in the browser'"),
  ("finch",2.5,6.0,"H2 on finch3d.com: 'Test thousands of design options to understand trade-offs with real-time data'"),
  ("bentley",3.5,7.0,"meta title, bentley.com/software/civil-worksuite/: 'Civil WorkSuite: Site Design Software' (title only; body copy unreadable)"),
  ("archistar",6.5,6.0,"meta on archistar.ai: 'Trusted by Los Angeles and Austin to cut permit approval times by up to 55%.'"),
  ("architechtures",4.0,3.0,"H1 on architechtures.com: 'Generate optimal building designs in real-time'"),
  ("maket",1.5,3.8,"H1 on maket.ai: 'The AI Home Design Studio'; H2: 'The future of home design' - a studio, not a single study"),
  ("zenerate",8.5,4.0,"meta on zenerate.ai: 'Generate site plans, floor plans, parking layouts, and pro formas to make faster and smarter land development decisions.'"),
  ("arkdesign",8.0,3.5,"H2 on arkdesign.ai: 'Generate More Profit'"),
  ("deepblocks",9.5,5.0,"H3 on deepblocks.com: 'a variance scenario reaching a 42% return on cost'"),
  ("landtech",9.0,8.5,"H1 on land.tech: 'All Your Land Decisions, Powered by One Intelligent Platform.'; H3: 'build profitable, compliant schemes'"),
  ("modelur",3.5,2.5,"meta on modelur.com: 'calculates key urban parameters in real-time'; H2: 'SketchUp Supercharged'"),
  ("hektar",6.0,3.0,"meta on hektar.ai: 'generates volume studies, density scenarios and KPIs for raw land in minutes'"),
  ("esri",3.0,8.5,"meta on esri.com ArcGIS Urban: 'Optimize cities, analyze data & create sustainable environments'"),
  ("urbansim",3.5,6.0,"meta on urbansim.com: 'helps cities and developers to build smarter and more sustainable cities, and reduce costs'"),
  ("sketchup",2.0,6.5,"meta on sketchup.com: 'Design in 3D, from concept to construction'"),
  ("vectorworks",1.5,6.0,"meta on vectorworks.net/landmark: 'transform your design, presentation, irrigation, and documentation workflows'"),
  ("aprao",10.0,4.0,"H1 on aprao.com: 'Assess every real estate deal with confidence'; H2: 'The financial-modelling engine for the AI era'"),
  ("landchecker",7.5,6.5,"H2 on landchecker.com.au: 'The complete property intelligence platform'"),
  ("urbanfootprint",4.5,7.5,"meta on urbanfootprint.com: 'Assess risk and make data-driven decisions with the most powerful urban, climate, and community resilience decision intelligence platform.'"),
  ("geopogo",2.8,2.0,"meta on geopogo.com: 'Design and edit Revit models with Claude AI - and download real-world 3D city models in seconds.'"),
  ("skema",3.0,5.0,"H1 on skema.ai: 'Generative Design for AEC'; H2: 'Design Intent Doesn't Survive the Handoff'"),
  ("civilsai",7.0,3.0,"H2 on civils.ai: 'Estimate your ROI in seconds.'; meta: 'Cut takeoff time by up to 90%'"),
  ("transoft",3.4,6.1,"meta on transoftsolutions.com: 'help professionals plan, design, and operate safe transportation systems'"),
  ("rhino",2.0,5.0,"meta on rhino3d.com: 'Rhinoceros 3D: Design, Model, Present, Analyze, Realize...'"),
 ],
 "The market splits cleanly on what the early study is for, and the anchor sits at the far performance end: Forma is one of only two sites in thirty that mention wind at all, and the only one selling that as the reason to decide early. The right-hand column - Aprao, Deepblocks, Zenerate, ArkDesign, LandTech - argues the opposite, that the early study is an underwriting exercise. Top-left, design-led platforms with real breadth, is thin: Snaptrude and SketchUp are there, Forma is on its edge, and it is the quadrant Autodesk is best equipped to own. The crowded corner is bottom-right, single-purpose feasibility calculators, where five companies are selling nearly the same sentence."))

# ---------------------------------------------------------------- 2 buyer
matrices.append(M(
 "buyer", "Who the copy says it is for",
 "The same software gets sold to a lone architect, a deal team, or a city. That choice sets the price, the proof and the sales motion.",
 "Institutional weight of the buyer", "an individual practitioner", "an institution: enterprise, city, agency",
 "Breadth of the discipline addressed", "one discipline's work", "design, finance and planning together",
 {"tl": "Cross-discipline for small teams", "tr": "Institutional platforms",
  "bl": "Practitioner tools", "br": "Departmental tools"},
 [
  ("forma",5.0,4.0,"meta on blogs.autodesk.com/forma: 'Autodesk's blog for architects and designers - covering early-stage design workflows'"),
  ("testfit",6.0,7.5,"H2 on testfit.io: 'Built for the Deal Team'"),
  ("giraffe",9.0,9.5,"H3 on giraffe.build: 'For Local Governments & Municipalities'; 'Enterprise Decision System'; meta: 'across feasibility, planning, design and finance'"),
  ("snaptrude",4.0,4.0,"title on snaptrude.com: 'The AI-Powered BIM software for Architects'"),
  ("dbf",9.5,7.0,"meta on digitalbluefoam.com: 'spatial reasoning AI for cities, governments and asset owners'"),
  ("hypar",4.0,3.0,"hypar.io/llms.txt: 'Studio tier for firms standardizing on Hypar'"),
  ("finch",5.0,4.0,"H3 on finch3d.com: 'Built by architects, for the way AEC professionals actually design and make decisions.'"),
  ("bentley",8.0,5.0,"meta title, bentley.com/software/opensite-plus/: 'OpenSite+: AI-Powered Site Design Software | Bentley Systems' (title only)"),
  ("archistar",9.5,5.0,"meta on archistar.ai: 'AI plan review and permitting software for local governments.'"),
  ("architechtures",3.0,3.0,"meta on architechtures.com: 'AI Architecture Generator. Reduces architectural design time.'"),
  ("maket",1.0,2.0,"H2 on maket.ai: 'Anyone can design a home'"),
  ("zenerate",4.0,6.5,"H2 on zenerate.ai: 'site plans, floor plans, and parking layouts with pro forma insights for faster land development'"),
  ("arkdesign",3.5,6.0,"meta on arkdesign.ai: 'A tool for architects and real estate developers.'"),
  ("deepblocks",5.0,7.5,"H3 on deepblocks.com: 'with program, cost, revenue, and return assumptions already organized for deeper underwriting'"),
  ("landtech",7.0,8.5,"H2 on land.tech: 'Built for every type of land professional .'; meta: 'planning, constraints, data and insight into one powerful platform'"),
  ("modelur",2.0,2.5,"H2 on modelur.com: 'What Architects Say About Modelur?'"),
  ("hektar",4.0,5.5,"meta on hektar.ai: 'Used by developers, architects, and municipalities across the Nordics.'"),
  ("esri",9.5,7.0,"H2 on esri.com: 'Collaborative urban planning'; 'Project e-submission'"),
  ("urbansim",9.0,6.0,"meta on urbansim.com: 'helps cities and developers to build smarter and more sustainable cities'"),
  ("sketchup",4.0,3.0,"meta on sketchup.com: 'intuitive tools for architects, designers, and builders'"),
  ("vectorworks",4.0,4.5,"meta on vectorworks.net/landmark: 'design, presentation, irrigation, and documentation workflows'"),
  ("aprao",6.0,3.5,"H2 on aprao.com: 'Enterprise-grade security, by default'"),
  ("landchecker",5.5,5.0,"meta on landchecker.com.au: 'Trusted by thousands of businesses every day.'"),
  ("urbanfootprint",9.0,6.5,"H2 on urbanfootprint.com: 'Empower decision making with actionable insight across industries and use cases'"),
  ("geopogo",2.5,3.0,"meta on geopogo.com: 'AI-powered architecture tools for Revit, Unreal Engine, Blender, SketchUp & more'"),
  ("skema",6.0,4.5,"H2 on skema.ai: 'What the Industry Is Saying.'; H1: 'Generative Design for AEC'"),
  ("civilsai",5.0,3.5,"meta on civils.ai: 'AI quantity takeoffs for groundworks contractors'"),
  ("transoft",7.5,4.0,"H1 on transoftsolutions.com: 'Innovative Solutions for Transportation Professionals'"),
  ("rhino",2.0,3.5,"meta on rhino3d.com: 'Rhinoceros 3D: Design, Model, Present, Analyze, Realize...'"),
 ],
 "Two separate businesses are visible here. Bottom-left holds practitioner tools sold one seat at a time - Maket, Modelur, Rhino, Geopogo, Architechtures - and top-right holds institutional platforms: Esri, Archistar, Giraffe, UrbanFootprint, Digital Blue Foam, all naming cities or agencies in their meta descriptions. Forma sits in the middle of both axes, and that is the honest reading: its copy names 'architects and designers', a discipline and a practitioner, while its commercial reality is a firm-wide Autodesk agreement. Nobody in the corpus is selling cross-discipline breadth to individual practitioners, which is probably a real constraint rather than white space - the finance and planning halves are bought by different people."))

# ---------------------------------------------------------------- 3 offering
matrices.append(M(
 "handoff", "Where the work stops, and how much the machine does",
 "Early-phase tools all end somewhere. The vendor that carries further downstream competes with BIM; the one that stops at concept has to survive the handoff.",
 "How far the work is carried", "stops at concept or feasibility", "through to BIM and construction documents",
 "How much the software decides", "assists you while you model", "generates the scheme for you",
 {"tl": "Generators", "tr": "Automated production",
  "bl": "Modelling environments", "br": "Documentation suites"},
 [
  ("forma",4.0,6.0,"H2 on blogs.autodesk.com/forma: 'How does Forma Site Design work with Revit and other tools?'; 'Smarter Generative...'"),
  ("testfit",3.0,9.0,"H1 on testfit.io: 'Automate Site Plans. Accelerate Decisions.'"),
  ("giraffe",3.5,7.0,"H2 on giraffe.build: 'Giraffe is the unifying platform to systematically automate tasks across your entire workflow.'"),
  ("snaptrude",8.5,7.0,"meta on snaptrude.com: 'Concept to BIM-ready models in your browser.'; '10 AI agents'"),
  ("dbf",2.5,8.0,"H2 on digitalbluefoam.com: 'Ask a real spatial question Get a defensible answer'"),
  ("hypar",5.0,5.0,"meta on hypar.io: 'Import site and Revit data, edit with automatic measurement, export to Revit.'"),
  ("finch",6.0,8.5,"H2 on finch3d.com: 'Test thousands of design options...'; 'Refine with precision'; 'Deliver faster'"),
  ("bentley",9.0,7.0,"meta title, blog.bentley.com: 'The First AI-driven Civil Engineering Software for Site Design' (title only)"),
  ("archistar",4.0,7.0,"H2 on archistar.ai: 'Standardized assessment in minutes'"),
  ("architechtures",4.0,9.0,"H1 on architechtures.com: 'Generate optimal building designs in real-time'"),
  ("maket",2.0,8.5,"meta on maket.ai: 'generate floor plans, edit by chat, and visualize your space in minutes'"),
  ("zenerate",3.0,9.0,"H2 on zenerate.ai: 'Instantly generate optimized site plans, floor plans, and parking layouts'"),
  ("arkdesign",4.5,8.5,"H1 on arkdesign.ai: 'AI-Powered Design & Feasibility Studies'; H2: 'Up to code'"),
  ("deepblocks",1.5,6.0,"H3 on deepblocks.com: 'Developer exports each model's assumptions and outputs as a CSV'"),
  ("landtech",1.5,5.0,"H2 on land.tech: 'Meet the LandTech AI Assistant.'"),
  ("modelur",2.5,4.0,"H1 on modelur.com: 'Fast and Accurate 3D Massing and Feasibility Studies'; H2: 'SketchUp Supercharged'"),
  ("hektar",2.0,7.5,"H1 on hektar.ai: 'Explore your site. Volume studies in minutes.'"),
  ("esri",4.0,4.0,"H2 on esri.com: '3D scenario modeling'; 'Data-driven analysis'"),
  ("urbansim",2.0,5.0,"H2 on urbansim.com: 'PLAN INTELLIGENTLY'"),
  ("sketchup",7.5,1.5,"meta on sketchup.com: 'Design in 3D, from concept to construction, with intuitive tools'"),
  ("vectorworks",9.5,2.0,"meta on vectorworks.net/landmark: 'your design, presentation, irrigation, and documentation workflows'"),
  ("aprao",1.0,4.0,"H2 on aprao.com: 'Everything you need to run your numbers with confidence'"),
  ("landchecker",1.0,2.0,"H2 on landchecker.com.au: 'Title Searches'; 'Property Reports'"),
  ("urbanfootprint",1.5,3.0,"H2 on urbanfootprint.com: 'Explore Resilience Insights and bring data to life with our intuitive and scalable web-based application'"),
  ("geopogo",6.0,6.0,"meta on geopogo.com: 'Design and edit Revit models with Claude AI'"),
  ("skema",7.0,7.5,"H2 on skema.ai: 'Your New BIM Workflow'; 'Design Intent Doesn't Survive the Handoff'"),
  ("civilsai",6.0,7.0,"H1 on civils.ai: 'Accurate AI Takeoffs & Checks before your project breaks ground.'"),
  ("transoft",7.0,3.0,"meta on transoftsolutions.com: 'plan, design, and operate safe transportation systems'"),
  ("rhino",6.0,1.0,"H1 on rhino3d.com: 'Rhino 8'; meta: 'Design, Model, Present, Analyze, Realize...'"),
 ],
 "The generators cluster hard in the top-left: TestFit, Zenerate, Architechtures, ArkDesign, Maket and Hektar all promise a scheme in minutes and all stop before documentation. The bottom-right - carry it all the way, but you do the drawing - is the incumbents' ground, Vectorworks, SketchUp and Rhino. Only three sites claim both automation and downstream delivery: Snaptrude, Skema and Bentley, and they are the ones that make the handoff itself the argument ('Design Intent Doesn't Survive the Handoff'). Forma sits mid-left, generating analysis rather than geometry and explicitly handing to Revit - which is a deliberate position inside a suite, not a gap, but it does mean Snaptrude is attacking the exact seam Autodesk chose to leave open."))

# ---------------------------------------------------------------- 4 messaging
matrices.append(M(
 "proof", "How they argue: evidence versus vocabulary",
 "In a young category, vendors either prove the claim with named customers and numbers, or they win by naming the category themselves. Few do both.",
 "Proof on the page", "adjectives and capability lists", "named customers, cities, percentages",
 "Category stance", "uses the market's existing words", "coins its own noun for what it is",
 {"tl": "Category creators", "tr": "Proven category creators",
  "bl": "Conventional tools", "br": "Proven conventional tools"},
 [
  ("forma",6.5,4.0,"H2 on blogs.autodesk.com/forma: 'Forma Site Design wins Architectural Record 2025 Architectural Products of the Year!'"),
  ("testfit",8.0,3.0,"H2 on testfit.io: 'Users Win Deals with TestFit'; 'As seen in'; title: 'Real Estate Feasibility Platform'"),
  ("giraffe",3.5,9.5,"title on giraffe.build: 'The Orchestration Layer for AI-Driven Real Estate'; H3: 'Enterprise Decision System'"),
  ("snaptrude",5.0,2.0,"title on snaptrude.com: 'The AI-Powered BIM software for Architects'"),
  ("dbf",4.5,9.0,"H1 on digitalbluefoam.com: 'Your spatial reasoning layer for every asset decision.'; H2: 'The spatial memory beneath it is the moat'"),
  ("hypar",4.0,6.0,"title on hypar.io: 'Hypar | Space Planning Software for Building Buy-In'"),
  ("finch",3.5,6.0,"H2 on finch3d.com: 'Used by AEC professionals worldwide'; 'AI-native platform for building design'"),
  ("bentley",4.0,1.5,"meta title: 'OpenSite+: AI-Powered Site Design Software | Bentley Systems' (title only)"),
  ("archistar",9.5,5.5,"H2 on archistar.ai: 'AI PreCheck is trusted by 30-plus cities and local governments worldwide'; meta: 'cut permit approval times by up to 55%'"),
  ("architechtures",3.0,4.0,"H1 on architechtures.com: 'AI Architecture Generator in Real-Time'"),
  ("maket",3.0,5.0,"H1 on maket.ai: 'The AI Home Design Studio'"),
  ("zenerate",3.5,2.0,"title on zenerate.ai: 'AI Feasibility Study Tool for Land Development'"),
  ("arkdesign",6.5,3.0,"H2 on arkdesign.ai: 'How industry leaders are using ARK'; named: 'Fariba Makooi, Principal | Fischer+Makooi Architects'"),
  ("deepblocks",8.5,4.0,"H3 on deepblocks.com: 'Existing market for sale, in a prime Little Havana corner... yielding an 8.44% return on cost.'"),
  ("landtech",5.0,4.0,"H2 on land.tech: 'Helping teams move faster, with confidence .'; H1: 'One Intelligent Platform'"),
  ("modelur",5.5,3.0,"H2 on modelur.com: 'What Architects Say About Modelur?'; title: 'Urban Design Software - Modelur'"),
  ("hektar",5.5,4.0,"meta on hektar.ai: 'Used by developers, architects, and municipalities across the Nordics.'"),
  ("esri",5.0,2.0,"title on esri.com: 'Urban Planning, Design & Development Software | ArcGIS Urban'"),
  ("urbansim",5.0,3.0,"about page on urbansim.com carries the stat blocks '80M' and '10,000'"),
  ("sketchup",6.0,2.0,"H2 on sketchup.com: 'See what customers are saying'; 'Empowering the people building our world'"),
  ("vectorworks",3.5,2.5,"H1 on vectorworks.net: 'THE ULTIMATE LANDSCAPE DESIGN SOFTWARE'"),
  ("aprao",5.5,4.5,"H2 on aprao.com: 'What our customers say'; 'The financial-modelling engine for the AI era'"),
  ("landchecker",8.0,4.0,"meta on landchecker.com.au: 'Trusted by thousands of businesses every day.'"),
  ("urbanfootprint",3.5,8.5,"title on urbanfootprint.com: 'The Resilient Decision Intelligence Platform'"),
  ("geopogo",3.0,6.0,"title on geopogo.com: 'Geopogo - AI for Architecture: Claude to Revit & 3D City Models'"),
  ("skema",4.5,6.0,"H2 on skema.ai: 'What the Industry Is Saying.'; H1: 'Generative Design for AEC'"),
  ("civilsai",8.0,3.0,"meta on civils.ai: 'Cut takeoff time by up to 90%'; H2: 'What our clients say.'"),
  ("transoft",6.0,3.0,"H2 on transoftsolutions.com: 'Empowering Transportation Professionals Since 1991'"),
  ("rhino",4.5,2.0,"H1 on rhino3d.com: 'Rhino 8'"),
 ],
 "Only one company occupies the top right - a category it named, backed by proof anyone can check - and it is Archistar, whose coined noun is a feature name ('AI PreCheck') rather than a claim on the market. The three companies that have genuinely renamed the category, Giraffe ('orchestration layer'), Digital Blue Foam ('spatial reasoning layer') and UrbanFootprint ('decision intelligence'), all argue with adjectives; the four with hard numbers on the page - Archistar, Deepblocks, Landchecker, Civils.ai - describe themselves in the market's ordinary words. Forma is the interesting middle case: it holds the strongest single proof point in the corpus, Architectural Record's 2025 product of the year, and it is spending that credibility on a category name it has just walked away from, having renamed from Forma to Forma Site Design and moved towards the market's vocabulary."))

# ---------------------------------------------------------------- 5 commercial
priced = [
  ("forma",8.0,6.0,"meta title on autodesk.com/products/forma-site-design/free-trial: 'Try Autodesk Forma Site Design | A Free 30-Day Trial' - Autodesk publishes list prices, though the page itself was unreadable from here"),
  ("testfit",8.0,7.0,"pricing page on testfit.io carries '$0 /mo', '$ 200', '$ 300' and a '$10,000' figure"),
  ("giraffe",2.0,6.0,"pricing page on giraffe.build offers only 'contact sales' and 'no credit card'"),
  ("snaptrude",9.0,2.5,"pricing page on snaptrude.com: '$0', '$60 /month', '$100 /month'"),
  ("dbf",1.0,8.0,"pricing page on digitalbluefoam.com offers only 'contact sales' / 'talk to sales'"),
  ("hypar",9.0,4.0,"hypar.io/llms.txt: 'plans and pricing, $100 per user per month, Studio tier for firms standardizing on Hypar'"),
  ("finch",7.0,8.0,"pricing page on finch3d.com: 'EUR 79' and 'EUR 14,500'"),
  ("bentley",1.0,8.0,"no pricing reachable: every www.bentley.com path redirects to a sign-in gate from here"),
  ("archistar",8.0,5.0,"pricing page on archistar.ai: '$95', '$345/mo', '$595'"),
  ("architechtures",9.0,4.0,"pricing page on architechtures.com: '$ 49', '$ 294', '$ 588', '$ 3,528'"),
  ("maket",9.5,1.0,"pricing page on maket.ai: '$0 / month', '$20 / month', '$100 / month'"),
  ("zenerate",3.0,6.0,"pricing page on zenerate.ai shows 'Subscription Plans' and a free trial but no figures"),
  ("arkdesign",1.0,5.0,"no pricing page found on arkdesign.ai; the CTA is 'Get Certified and be Featured in Our Gallery'"),
  ("deepblocks",8.5,6.0,"pricing page on deepblocks.com: '$ 55.55 per month', '$499/mo', '$1,999/mo', '$3,999/mo'"),
  ("landtech",8.0,5.0,"pricing page on land.tech: 'GBP 150 / month'"),
  ("modelur",9.2,3.5,"pricing page on modelur.com: 'EUR 0', 'EUR 74 PER SEAT', 'EUR 149 PER SEAT'"),
  ("hektar",2.0,5.0,"pricing page on hektar.ai offers only 'talk to sales'"),
  ("esri",3.0,7.0,"esri.com ArcGIS Urban pages offer a free trial; no figure on the product pages scanned"),
  ("urbansim",1.0,6.0,"no pricing page on urbansim.com (probed and absent)"),
  ("sketchup",9.5,2.0,"pricing page on sketchup.com: '$10.75', '$30', '$33.25', '$40'"),
  ("vectorworks",3.0,5.0,"vectorworks.net shows 'Free Trial' and 'Buy Now' CTAs but no figure on the pages scanned"),
  ("aprao",3.0,4.0,"pricing page on aprao.com offers a free trial; no figures on the page"),
  ("landchecker",8.8,4.2,"pricing page on landchecker.com.au: '$0', '$200', '$240', '$2,400/year'"),
  ("urbanfootprint",2.0,7.0,"pricing page on urbanfootprint.com carries no figures"),
  ("skema",8.5,5.0,"pricing page on skema.ai: '$199 / month', '$750 / month'"),
  ("civilsai",8.5,4.0,"pricing page on civils.ai: '$ 90 / month', '$ 270 / month'"),
  ("transoft",1.0,6.0,"no pricing page on transoftsolutions.com (probed and absent)"),
]
matrices.append(M(
 "commercial", "How they ask to be bought",
 "A published price is a claim that the buyer can decide alone. Hiding it is a claim that the sale needs a conversation - and in this market the two map onto very different products.",
 "Price transparency", "contact sales only", "full price published",
 "Entry price point", "free or low tens per month", "thousands, enterprise agreement",
 {"tl": "Enterprise, quote-led", "tr": "Published enterprise pricing",
  "bl": "Free and self-serve", "br": "Self-serve professional tools"},
 priced,
 "The diagonal here is real and it is the market's fault line: the cheap tools publish (Maket, SketchUp, Modelur, Snaptrude, Landchecker at the bottom right) and the expensive ones do not (Bentley, Digital Blue Foam, UrbanFootprint, Esri, UrbanSim, top left). Four companies break the line and they are the ones worth watching - Finch, TestFit, Deepblocks and Forma all publish a price and still ask for real money. Forma's position is a genuine advantage in a market where the direct alternatives at its price point mostly want a sales call; the two companies most often named against it, Giraffe and Hektar, both hide their pricing entirely. Rhino and Geopogo are off this chart: neither published a figure the scan could read, and inventing one would be guessing."))

# ---------------------------------------------------------------- 6 data / scale
matrices.append(M(
 "evidence", "What the software knows before you start",
 "An early-phase answer is only as good as the context behind it. Some vendors ship the world's data with the tool; others expect you to bring the site.",
 "Built-in context data", "you bring the site and the geometry", "parcels, zoning and GIS layers included",
 "Scale it addresses", "a single site", "a city or a portfolio",
 {"tl": "City-scale modelling", "tr": "Data platforms",
  "bl": "Site modelling tools", "br": "Site intelligence tools"},
 [
  ("forma",6.5,3.5,"H2 on blogs.autodesk.com/forma product page: 'Bases' and 'Proposal layers' among 'Forma Site Design's tools'; zoning appears once in the blog copy"),
  ("testfit",6.0,3.0,"'parcel' appears in testfit.io copy; H2: 'Minimize Earthwork Cost with Automatic Cut and Fill'"),
  ("giraffe",9.0,8.0,"H3 on giraffe.build: 'Combine thousands of spatial layers, workflows, and apps into a repeatable decision process'"),
  ("snaptrude",5.0,2.5,"meta on snaptrude.com: '10 AI agents for zoning, site analysis, massing, floor plans & more'"),
  ("dbf",8.5,9.0,"H2 on digitalbluefoam.com: 'Anyone can call an LLM The spatial memory beneath it is the moat'; 'One reasoning Any scale'"),
  ("hypar",4.0,2.0,"meta on hypar.io: 'Import site and Revit data, edit with automatic measurement'"),
  ("finch",2.0,5.0,"H3 on finch3d.com: 'Master plan' among typologies; no context-data claim in the copy"),
  ("archistar",7.0,7.0,"H2 on archistar.ai: 'AI PreCheck is trusted by 30-plus cities'; 'Standardized assessment in minutes'"),
  ("architechtures",1.5,2.0,"meta on architechtures.com: 'AI Architecture Generator. Reduces architectural design time.'"),
  ("maket",1.0,1.0,"meta on maket.ai: 'generate floor plans, edit by chat, and visualize your space in minutes'"),
  ("zenerate",5.0,2.5,"meta on zenerate.ai: 'Generate site plans, floor plans, parking layouts, and pro formas'"),
  ("arkdesign",5.0,2.0,"H2 on arkdesign.ai: 'Up to code'"),
  ("deepblocks",9.5,7.0,"deepblocks.com copy uses 'zoning' six times; H3: 'a variance scenario reaching a 42% return on cost'"),
  ("landtech",9.5,7.0,"meta on land.tech: 'LandTech brings planning, constraints, data and insight into one powerful platform for UK developers.'"),
  ("modelur",3.0,3.5,"meta on modelur.com: 'calculates key urban parameters in real-time'"),
  ("hektar",6.0,3.0,"meta on hektar.ai: 'generates volume studies, density scenarios and KPIs for raw land'"),
  ("esri",10.0,9.0,"esri.com ArcGIS Urban copy uses 'GIS' 23 times; H2: 'Data-driven analysis'"),
  ("urbansim",8.0,9.5,"H2 on urbansim.com: 'PLAN COLLABORATIVELY'; meta: 'the leading AI-driven platform for sustainable urban planning'"),
  ("sketchup",2.0,3.0,"meta on sketchup.com: 'Design in 3D, from concept to construction'"),
  ("vectorworks",3.0,3.0,"meta on vectorworks.net/landmark: 'from plant selection and sustainability assessments to BIM collaboration and reporting'"),
  ("aprao",3.0,4.0,"H2 on aprao.com: 'Everything you need to run your numbers with confidence'"),
  ("landchecker",10.0,5.0,"H2 on landchecker.com.au: 'Planning Zones, Overlays and Layers'; 'Title Searches'; 'Unlimited High-Resolution Aerial Imagery'"),
  ("urbanfootprint",9.0,9.5,"H3 on urbanfootprint.com: 'Climate Risk & Sustainability'; meta: 'urban, climate, and community resilience'"),
  ("geopogo",6.0,5.0,"meta on geopogo.com: 'download real-world 3D city models in seconds'"),
  ("skema",1.5,3.0,"H2 on skema.ai: 'Put Your Proven Designs Back to Work !'"),
  ("civilsai",3.0,2.0,"meta on civils.ai: 'Measure earthworks, drainage, concrete & more.'"),
  ("transoft",4.0,6.0,"meta on transoftsolutions.com: 'plan, design, and operate safe transportation systems'"),
  ("rhino",1.0,3.0,"meta on rhino3d.com: 'Rhinoceros 3D: Design, Model, Present, Analyze, Realize...'"),
 ],
 "This is where the anchor's real exposure shows. The bottom-right quadrant - deep context data applied to a single site - is where an early-phase site tool ought to be strongest, and it is owned by companies that do no design at all: Landchecker, Deepblocks, LandTech. Forma sits just inside it but well short of them, because its copy talks about its own tools ('Bases', 'Proposal layers') rather than about the parcel, zoning and title data a developer needs before the massing means anything. Top-right is the GIS establishment, Esri and UrbanSim and UrbanFootprint, at a scale above any single project. Bentley and cove.tool are absent from this chart: neither site would give up enough copy to place them honestly."))

data = {
 "anchor": {"id": "forma", "name": "Autodesk Forma Site Design", "domain": "autodesk.com"},
 "market_definition":
   "Software that compresses the earliest phase of a building project - the weeks between "
   "acquiring a site and committing to a scheme - into hours. The companies call it site "
   "design, site planning, feasibility, volume studies, massing, or early-phase design, and "
   "the choice of noun is itself the positioning. Running through the market is one "
   "disagreement: whether the early study exists to establish how a place will perform - "
   "sun, wind, noise, density, carbon - or to establish whether the deal makes money. "
   "Autodesk Forma Site Design is the clearest statement of the first position; Aprao, "
   "Deepblocks and TestFit are the clearest statements of the second. A second, quieter "
   "split runs underneath: who owns the context data the answer depends on.",
 "generated_at": datetime.date.today().isoformat(),
 "companies": companies,
 "matrices": matrices,
 "takeaways": [
   "Forma's signature capability is almost uncontested in stated positioning: of 30 companies, "
   "one other mentions carbon, one mentions wind, and none mention noise, daylight or "
   "microclimate anywhere in their marketing copy. Either environmental performance is a real "
   "moat that nobody else is even claiming, or the market has decided buyers do not choose on "
   "it - and the answer to that question should drive the messaging.",
   "The competitive set has quietly reorganised around money. TestFit, Zenerate, ArkDesign, "
   "Deepblocks, LandTech and Aprao all lead with pro forma, yield, profit or return on cost. "
   "Forma leads with design quality and analysis. These are not the same product being sold "
   "differently; they are different answers to what the early phase is for.",
   "'AI' is dead as a differentiator here - 27 of 30 sites use it. 'Generative' is used by only "
   "four. The words that still separate companies are the specific nouns: pro forma, zoning, "
   "parcel, grading, buy-in, spatial reasoning.",
   "Snaptrude is the most direct strategic threat in the corpus, because it attacks the seam "
   "Forma deliberately leaves open: 'From brief to BIM, in one connected model' is an argument "
   "against the Forma-to-Revit handoff, sold to Forma's exact stated buyer (architects) at "
   "$60-$100 per month against Forma's roughly $185.",
   "Bentley owns the literal phrase. 'OpenSite+: AI-Powered Site Design Software' and 'Civil "
   "WorkSuite: Site Design Software' mean Autodesk's rename to 'Forma Site Design' walks into "
   "an SEO and category fight with a competitor already using those words for a product that "
   "produces construction documents.",
   "The open position on the messaging chart is a named category backed by hard proof. Everyone "
   "who has coined a category noun (Giraffe, Digital Blue Foam, UrbanFootprint) argues with "
   "adjectives; everyone with named customers and percentages (Archistar, Deepblocks, "
   "Landchecker, Civils.ai) describes themselves in ordinary words. Forma has the strongest "
   "single proof point in the corpus - Architectural Record's 2025 product of the year - and "
   "the reach to use it.",
 ],
 "sources": [
   {"url": "https://www.autodesk.com/products/forma-site-design/overview", "used_for": "anchor identity; meta title only - the page returns HTTP 403 to this network"},
   {"url": "https://blogs.autodesk.com/forma/", "used_for": "anchor body copy (Autodesk's own Forma blog)"},
   {"url": "https://blogs.autodesk.com/forma/2026/08/20/what-is-forma-site-design/", "used_for": "anchor category language"},
   {"url": "https://www.parametric.se/post/comparing-early-stage-feasibility-tools-2026-forma-giraffe-finch-testfit-hektar", "used_for": "level-1 roster"},
   {"url": "https://www.g2.com/products/autodesk-forma/competitors/alternatives", "used_for": "level-1 roster (names only; construction-PM results discarded as the wrong category)"},
   {"url": "https://www.cbinsights.com/company/giraffe-technology/alternatives-competitors", "used_for": "level-2 roster"},
   {"url": "https://www.cbinsights.com/company/spacemaker/alternatives-competitors", "used_for": "level-2 roster (Spacemaker is Forma's former name)"},
   {"url": "https://www.nomic.ai/compare/testfit-alternatives", "used_for": "level-2 roster"},
   {"url": "https://hypar.io/llms.txt", "used_for": "Hypar positioning and pricing (first-party, robots-permitted)"},
   {"url": "https://www.bentley.com/software/opensite-plus/", "used_for": "Bentley meta title only - the site serves a sign-in gate to this network"},
 ],
}

out = pathlib.Path('forma-site-design/analysis.json')
out.write_text(json.dumps(data, indent=2, ensure_ascii=False))
print("wrote %s: %d companies, %d matrices, %d points"
      % (out, len(companies), len(matrices), sum(len(m['points']) for m in matrices)))
