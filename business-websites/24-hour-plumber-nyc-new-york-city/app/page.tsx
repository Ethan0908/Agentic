import Image from "next/image";
import data from "../business.json";

const company = data.company;
const places = data.places_data;

const phoneDisplay = places.national_phone || company.phone;
const phoneHref = `tel:${(places.international_phone || company.phone).replace(
  /[^\d+]/g,
  "",
)}`;
const city = "New York City";

const listingDetails = [
  ["Phone", phoneDisplay],
  ["Address", places.formatted_address],
  ["Category", places.google_primary_type_display.text],
];

const inquiryTypes = [
  {
    title: "Plumber Requests",
    copy: "The primary public listing category is Plumber. Call to describe the issue and confirm whether the request fits the services offered.",
  },
  {
    title: "Service Call Details",
    copy: "Use the phone call to confirm current availability, next steps, and the information needed for your location.",
  },
  {
    title: "Contractor Questions",
    copy: "The listing also appears under general contractor. Ask directly before assuming the scope of contractor-related work.",
  },
];

const callChecklist = [
  "Your address or nearest cross streets",
  "A short description of the plumbing request",
  "Any building access details that may affect timing",
  "Questions about current availability, pricing, and scope",
];

const faqs = [
  {
    question: "Are exact hours listed?",
    answer:
      "Exact hours are not included in the provided source data. Call for current availability.",
  },
  {
    question: "Is pricing published?",
    answer:
      "Pricing is not included in the provided listing. Call to ask for current details before scheduling.",
  },
  {
    question: "What area is shown in the listing?",
    answer:
      "The company data points to New York City and the listed address on Lexington Avenue. Confirm service details for your specific address by phone.",
  },
];

export default function HomePage() {
  return (
    <main>
      <section className="hero" aria-labelledby="home-title">
        <Image
          className="hero-image"
          src="/hero-plumbing.png"
          alt="Plumbing valves, pipes, and tools in a utility work area"
          fill
          priority
          sizes="100vw"
        />
        <div className="hero-scrim" />

        <header className="topbar" aria-label="Site header">
          <a className="brand" href="#home-title" aria-label={company.name}>
            <span className="brand-mark">24</span>
            <span>{company.name}</span>
          </a>
          <nav className="nav-links" aria-label="Primary navigation">
            <a href="#service-area">Service Area</a>
            <a href="#details">Details</a>
            <a href="#contact">Contact</a>
          </nav>
          <a className="top-call" href={phoneHref}>
            Call {phoneDisplay}
          </a>
        </header>

        <div className="hero-content">
          <p className="eyebrow">{city} Plumber Listing</p>
          <h1 id="home-title">{company.name}</h1>
          <p className="hero-copy">
            A plumber listing in {city} with a public address on Lexington
            Avenue. Call {phoneDisplay} to discuss your plumbing request,
            confirm current availability, and get the next step for your
            address.
          </p>
          <div className="hero-actions" aria-label="Main actions">
            <a className="button button-primary" href={phoneHref}>
              Call Now
            </a>
            <a className="button button-secondary" href="#details">
              View Listing Details
            </a>
          </div>
        </div>

        <aside className="hero-details" aria-label="Published listing details">
          <p className="detail-heading">Published Details</p>
          <dl>
            {listingDetails.map(([label, value]) => (
              <div key={label}>
                <dt>{label}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
        </aside>
      </section>

      <section className="service-strip" aria-label="Quick contact details">
        <div>
          <span>Phone</span>
          <a href={phoneHref}>{phoneDisplay}</a>
        </div>
        <div>
          <span>Address</span>
          <a href={places.google_maps_url}>{places.formatted_address}</a>
        </div>
        <div>
          <span>Website</span>
          <a href={places.website_uri}>24hourplumber.nyc</a>
        </div>
      </section>

      <section className="content-band split" id="service-area">
        <div>
          <p className="section-kicker">Service Area</p>
          <h2>Built around New York City calls.</h2>
        </div>
        <div className="section-copy">
          <p>
            The source listing identifies {company.name} as a plumber in{" "}
            {city}. Use the phone number to confirm service fit, current
            availability, and details for the specific address where help is
            needed.
          </p>
          <p>
            The listed address is {places.formatted_address}. If you plan to
            visit or send mail, call first to confirm the right next step.
          </p>
        </div>
      </section>

      <section className="content-band" aria-labelledby="inquiries-title">
        <div className="section-heading">
          <p className="section-kicker">What To Ask About</p>
          <h2 id="inquiries-title">Start with the public listing facts.</h2>
        </div>
        <div className="inquiry-grid">
          {inquiryTypes.map((item) => (
            <article className="inquiry-card" key={item.title}>
              <h3>{item.title}</h3>
              <p>{item.copy}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="prep-panel" aria-labelledby="prep-title">
        <div className="prep-intro">
          <p className="section-kicker">Before You Call</p>
          <h2 id="prep-title">Have the job basics ready.</h2>
          <p>
            A short, direct call is the cleanest way to confirm whether the
            request fits, what details are needed, and what current information
            applies.
          </p>
        </div>
        <ul className="checklist">
          {callChecklist.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="content-band faq-band" id="details">
        <div className="section-heading">
          <p className="section-kicker">Listing Details</p>
          <h2>Clear answers, no invented claims.</h2>
        </div>
        <div className="faq-list">
          {faqs.map((item) => (
            <article className="faq-item" key={item.question}>
              <h3>{item.question}</h3>
              <p>{item.answer}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="contact-band" id="contact" aria-labelledby="contact-title">
        <div>
          <p className="section-kicker">Contact</p>
          <h2 id="contact-title">Call 24 Hour Plumber NYC.</h2>
          <p>
            For current availability, service scope, pricing, or directions,
            use the published phone number or original website.
          </p>
        </div>
        <div className="contact-actions">
          <a className="button button-primary" href={phoneHref}>
            Call {phoneDisplay}
          </a>
          <a className="button button-dark" href={places.google_maps_url}>
            Open Map
          </a>
          <a className="text-link" href={places.website_uri}>
            Visit original website
          </a>
        </div>
        <address>
          {company.name}
          <br />
          {places.formatted_address}
          <br />
          <a href={phoneHref}>{phoneDisplay}</a>
        </address>
      </section>
    </main>
  );
}
