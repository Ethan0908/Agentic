import data from "../business.json";

const company = data.company;
const places = data.places_data;

const phoneDisplay = places.national_phone || company.phone;
const phoneHref = `tel:${company.phone.replace(/[^\d+]/g, "")}`;
const address = places.formatted_address || company.address;
const website = company.original_website;
const websiteDisplay = "https://dentist-holistic.com/";
const mapsUrl = places.google_maps_url;

const contactItems = [
  {
    label: "Phone",
    value: phoneDisplay,
    href: phoneHref,
  },
  {
    label: "Address",
    value: address,
    href: mapsUrl,
  },
  {
    label: "Original website",
    value: websiteDisplay,
    href: website,
  },
];

const callTopics = [
  {
    title: "Appointments",
    text: "Ask the office for current appointment availability and scheduling details.",
  },
  {
    title: "Dental care questions",
    text: "Confirm which dental services are currently offered and what information to bring.",
  },
  {
    title: "Visit planning",
    text: "Use the listed address on East 23rd Street and call for any current arrival instructions.",
  },
];

const planningNotes = [
  "Hours were not provided in the source data.",
  "Prices and insurance details were not provided in the source data.",
  "Call the office for current information before visiting.",
];

export default function HomePage() {
  return (
    <main className="site-shell">
      <header className="topbar" aria-label="Primary">
        <a className="brand" href="#top" aria-label={`${company.name} home`}>
          <span className="brand-mark">GS</span>
          <span>{company.name}</span>
        </a>
        <nav className="topnav" aria-label="Site links">
          <a href="#details">Details</a>
          <a href="#visit">Visit</a>
          <a href="#contact">Contact</a>
        </nav>
        <a className="top-call" href={phoneHref}>
          Call {phoneDisplay}
        </a>
      </header>

      <section className="hero" id="top">
        <img
          className="hero-image"
          src="/gramercy-dental-room.png"
          alt="A calm modern dental treatment room with natural light"
        />
        <div className="hero-content">
          <p className="eyebrow">Dentist in New York City</p>
          <h1>{company.name}</h1>
          <p className="hero-copy">
            A direct contact page for a dental practice at {address}. Call the
            office for current appointment details, available services, and
            visit information.
          </p>
          <div className="hero-actions" aria-label="Primary actions">
            <a className="button primary" href={phoneHref}>
              Call {phoneDisplay}
            </a>
            <a className="button secondary" href={mapsUrl} target="_blank" rel="noreferrer">
              Open map
            </a>
            <a className="button text-link" href={website} target="_blank" rel="noreferrer">
              Original website
            </a>
          </div>
          <p className="hero-address">{address}</p>
        </div>
      </section>

      <section className="quick-strip" aria-label="Known practice details">
        {contactItems.map((item) => (
          <a
            key={item.label}
            className="quick-item"
            href={item.href}
            target={item.label === "Phone" ? undefined : "_blank"}
            rel={item.label === "Phone" ? undefined : "noreferrer"}
          >
            <span>{item.label}</span>
            <strong>{item.value}</strong>
          </a>
        ))}
      </section>

      <section className="intro-section" id="details">
        <div className="section-kicker">Start with the facts</div>
        <div className="intro-grid">
          <div>
            <h2>Dental visit planning without guesswork.</h2>
            <p>
              The available listing identifies {company.name} as a dentist in
              New York City. Because specific hours, pricing, insurance details,
              and service menus were not provided, the clearest next step is to
              call the practice directly before planning a visit.
            </p>
          </div>
          <div className="detail-panel">
            <p className="panel-label">Listed business type</p>
            <strong>{company.industry_hint}</strong>
            <p>
              Located at {address}. The phone number and original website are
              available for current office information.
            </p>
          </div>
        </div>
      </section>

      <section className="topics-section">
        <div className="section-heading">
          <p className="section-kicker">What to confirm</p>
          <h2>Use the phone call to get the details that matter for your visit.</h2>
        </div>
        <div className="topic-grid">
          {callTopics.map((topic, index) => (
            <article className="topic-card" key={topic.title}>
              <span className="topic-number" aria-hidden="true">
                {String(index + 1).padStart(2, "0")}
              </span>
              <h3>{topic.title}</h3>
              <p>{topic.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="visit-section" id="visit">
        <div className="visit-copy">
          <p className="section-kicker">East 23rd Street</p>
          <h2>Keep the address, phone, map, and website in one place.</h2>
          <p>
            This page keeps the public listing details visible so it is easy to
            call, check the map, or continue to the practice website.
          </p>
        </div>
        <div className="visit-list" aria-label="Visit notes">
          {planningNotes.map((note) => (
            <div className="visit-note" key={note}>
              <span aria-hidden="true">-</span>
              <p>{note}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="contact-section" id="contact">
        <div className="contact-content">
          <p className="section-kicker">Contact</p>
          <h2>Call {company.name} for current information.</h2>
          <p>
            For appointment availability, office details, and questions about
            dental care, contact the practice directly.
          </p>
          <div className="contact-actions">
            <a className="button primary dark" href={phoneHref}>
              Call {phoneDisplay}
            </a>
            <a className="button secondary dark" href={mapsUrl} target="_blank" rel="noreferrer">
              Get directions
            </a>
          </div>
        </div>
        <address className="contact-card">
          <span>{company.name}</span>
          <a href={phoneHref}>{phoneDisplay}</a>
          <a href={mapsUrl} target="_blank" rel="noreferrer">
            {address}
          </a>
          <a href={website} target="_blank" rel="noreferrer">
            {websiteDisplay}
          </a>
        </address>
      </section>

      <footer className="footer">
        <span>{company.name}</span>
        <span>{address}</span>
      </footer>
    </main>
  );
}
