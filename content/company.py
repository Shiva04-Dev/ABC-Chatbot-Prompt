"""AfriBiz Connect content used to build the system prompt.

Kept as data, separate from application logic, so it can be edited without
touching any code. Sourced from AfriBiz_Knowledge.md (M8 go-live content).

Two things Shiv confirmed explicitly, overriding the more conservative
defaults this started with:
- DIRECTOR_NAME is the one staff member the bot may name (see the guardrail
  wording in app/prompts.py, which references this constant rather than a
  second hardcoded copy of the name).
- No exact pricing is included — costs depend on each client's requirements
  — so the tier breakdown below is paired with a "contact us for a quote"
  instruction in app/prompts.py instead of numbers.
"""

DIRECTOR_NAME = "Joshen (Josh) Indarjee"

COMPANY_DESCRIPTION = f"""Afribiz Connect (Pty) Ltd, trading as Afribiz Connect, is an international, multi-award-winning digital software and marketing agency based in South Africa (company registration 2020/510825/07, registered 1 July 2020), led by founder and director {DIRECTOR_NAME}. Positioning statement: "Urbanisation & Development Through Technology." Afribiz Connect combines technological expertise (including Information Systems Architecture, Data Engineering, and AI) with local market knowledge to help brands build "digital dominance" — the tools, strategy, and analytics needed to grow their brand and market position. It reaches roughly 1 million impressions weekly across its managed client portfolio.

Credentials: Level One B-BBEE contributor, 100% Black-Owned and 100% Black Designated Group Owned, certified B-BBEE Exempted Micro Enterprise (ICT sector); accredited Google Affiliate; Microsoft Accredited Partner; accredited affiliate of 22 On Sloane and YiEDI (Youth Innovation Entrepreneurship Design Institute).

Recognition: multiple awards including Nedbank's Hands Up For Small Business Winner, Most Empowering Software & Marketing Agency (International, 2025), Techpreneur of the Year (Africa, 2025), World Business Outlook's Best Software & Marketing Agency in Africa, Corporate Livewire's Digital Solutions of the Year (UK), and a place in Empire Magazine Africa's Nexus 100.

Locations: registered office in Verulam, KwaZulu-Natal, with additional presence in Umhlanga Ridge (Durban) and Bryanston (Johannesburg). Clients span retail, hospitality, security, logistics, healthcare, legal, financial services, government-linked entities, and township/informal-sector businesses, including engagements with Sentiv (formerly Altron Nexus), EDHE/USAf, and the HELM Programme, alongside a partnership network including Microsoft Africa, Telkom, Shell, and Nedbank.

Social impact: Afribiz Connect runs Kasi Digital Connect (bringing roughly 200 township businesses online per year) and Kasi 360 (a digital marketplace and business-support platform for township entrepreneurs and informal traders).

Brand pillars: Design, Innovate, Teamwork, Build."""

SERVICE_TIERS = """Tier 1: Graphic Design & Social Media Management, Brand Photography & Videography, Google Packages (Google Affiliate), Business Registration.

Tier 2 (Tier 1, plus): Website Development, Digital Audit & Strategy, Search Engine Optimisation (SEO).

Tier 3 (Tier 1 and Tier 2, plus): AI Solutions & Cybersecurity, App Development & Cloud Engineering, Brand Architecture & Style Guide, CRM System Implementation, PR, Events & 3D Mapping."""

CONTACT_DETAILS = """Phone / WhatsApp: +27 65 332 1150
Email: info@afribizconnect.co.za
Website: https://afribizconnect.co.za
Registered office: 46 Antelope Place, Mountview, Verulam, KwaZulu-Natal, 4339
Also based in: Umhlanga Ridge (Durban) and Bryanston (Johannesburg)
Social media: Facebook (facebook.com/afribizconnect), LinkedIn (linkedin.com/company/afribiz-connect), Instagram (@afribizconnect_), TikTok (@afribizconnect_)"""
