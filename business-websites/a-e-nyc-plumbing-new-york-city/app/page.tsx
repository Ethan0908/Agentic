import Image from "next/image";
import data from "../business.json";

const company = data.company;
const places = data.places_data;

const phoneDisplay = places.national_phone ?? company.phone;
const phoneHref = `tel:${company.phone.replace(/[^\d+]/g, "")}`;
const address = places.formatted_address ?? company.address;
const website = company.original_website ?? places.website_uri;
const mapsUrl = places.google_maps_url;

const callPrep = [
  "The property address, unit, floor, and best access point.",
  "Where the plumbing issue is happening and what has changed.",
  "Any building instructions, shutoff details, or timing constraints.",
];

const processSteps = [
  {
    title: "Call the main number",
    text: "Start with the listed phone number so current availability and the right next step can be confirmed.",
  },
  {
    title: "Share the site details",
    text: "Give the New York City address, building access notes, and a clear description of the plumbing request.",
  },
  {
    title: "Confirm the next move",
    text: "Ask for current information on service scope, timing, and any details needed before a visit or follow-up.",
  },
];

const faqs = [
  {
    question: "What area is listed for A&E NYC Plumbing?",
    answer:
      "The business data lists A&E NYC Plumbing in New York City, with an address at 40 Fulton St, New York, NY 10038.",
  },
  {
    question: "Are exact hours available here?",
    answer:
      "No exact hours were provided in the source data. Call the listed phone number for current availability.",
  },
  {
    question: "Can pricing be confirmed online?",
    answer:
      "No prices were provided in the source data. Call for current pricing, estimate, or visit details.",
  },
  {
    question: "Is there an email address?",
    answer:
      "No email address was included in the provided business data. Use the phone number or the original website.",
  },
];

export default function HomePage() {
  return (
    <main>
      <section className="top-strip" aria-label="Business contact summary">
        <div className="site-shell top-strip__inner">
          <span>New York City plumber</span>
          <span>40 Fulton St, New York, NY 10038</span>
          <a href={phoneHref}>{phoneDisplay}</a>
        </div>
      </section>

      <header className="site-header">
        <div className="site-shell header-grid">
          <a className="brand" href="#top" aria-label="A&E NYC Plumbing home">
            <span className="brand__mark">A&amp;E</span>
            <span>
              <strong>A&amp;E NYC Plumbing</strong>
              <small>Plumber · New York City</small>
            </span>
          </a>
          <nav className="nav-links" aria-label="Page sections">
            <a href="#details">Details</a>
            <a href="#process">Call Prep</a>
            <a href="#location">Location</a>
            <a href="#contact">Contact</a>
          </nav>
          <a className="header-call" href={phoneHref}>
            Call {phoneDisplay}
          </a>
        </div>
      </header>

      <section className="hero" id="top">
        <div className="site-shell hero-grid">
          <div className="hero-copy">
            <p className="eyebrow">Plumbing contact for New York City</p>
            <h1>Plumbing help starts with a direct NYC call.</h1>
            <p className="hero-lede">
              A&amp;E NYC Plumbing is listed as a plumber at 40 Fulton St in
              New York, NY. Call to confirm current availability, explain the
              plumbing request, and get the right next step.
            </p>
            <div className="hero-actions" aria-label="Primary actions">
              <a className="button button--primary" href={phoneHref}>
                Call {phoneDisplay}
              </a>
              <a
                className="button button--secondary"
                href={website}
                target="_blank"
                rel="noreferrer"
              >
                Original Website
              </a>
            </div>
            <dl className="hero-facts" aria-label="Company facts">
              <div>
                <dt>Phone</dt>
                <dd>
                  <a href={phoneHref}>{phoneDisplay}</a>
                </dd>
              </div>
              <div>
                <dt>Address</dt>
                <dd>{address}</dd>
              </div>
              <div>
                <dt>City</dt>
                <dd>New York City</dd>
              </div>
            </dl>
          </div>

          <div className="hero-media" aria-label="Plumbing workbench visual">
            <Image
              src="/images/plumbing-workbench-hero.png"
              alt="Plumbing fittings, pipework, and a pipe wrench on a work surface"
              width={1680}
              height={920}
              priority
            />
            <div className="hero-media__label">
              <span>Call for current availability</span>
              <strong>{phoneDisplay}</strong>
            </div>
          </div>
        </div>
      </section>

      <section className="intro-panel" id="details">
        <div className="site-shell intro-grid">
          <div>
            <p className="section-kicker">Straight information first</p>
            <h2>A practical contact point for plumbing requests in NYC.</h2>
          </div>
          <div className="intro-copy">
            <p>
              Plumbing issues usually need clear details before anyone can
              quote timing, scope, or next steps. This page keeps the verified
              information visible: A&amp;E NYC Plumbing, the listed phone
              number, the Fulton Street address, and the original website.
            </p>
            <p>
              If hours, prices, or specific services are important to your
              request, call for current information. Those details were not
              included in the provided business data.
            </p>
          </div>
        </div>
      </section>

      <section className="prep-section" id="process">
        <div className="site-shell split-layout">
          <div className="section-heading">
            <p className="section-kicker">Before you call</p>
            <h2>Have the building details ready.</h2>
            <p>
              New York City plumbing calls often depend on access, building
              rules, and a clear description of the issue. Having the basics
              ready makes the first conversation more useful.
            </p>
          </div>

          <div className="prep-list">
            {callPrep.map((item, index) => (
              <div className="prep-item" key={item}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <p>{item}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="process-band" aria-label="Contact process">
        <div className="site-shell">
          <div className="section-heading section-heading--wide">
            <p className="section-kicker">Simple call flow</p>
            <h2>Use the phone number to confirm what applies now.</h2>
          </div>
          <div className="process-grid">
            {processSteps.map((step, index) => (
              <article className="process-card" key={step.title}>
                <span className="process-card__number">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <h3>{step.title}</h3>
                <p>{step.text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="location-section" id="location">
        <div className="site-shell location-grid">
          <div className="location-copy">
            <p className="section-kicker">Listed location</p>
            <h2>Fulton Street address, New York City service context.</h2>
            <p>
              A&amp;E NYC Plumbing is listed at {address}. For service
              coverage, visit details, or current information for your exact
              address, use the phone number below.
            </p>
            <div className="location-actions">
              <a className="button button--primary" href={phoneHref}>
                Call {phoneDisplay}
              </a>
              <a
                className="button button--dark"
                href={mapsUrl}
                target="_blank"
                rel="noreferrer"
              >
                Open Map
              </a>
            </div>
          </div>
          <div className="service-area-box" aria-label="Service area details">
            <div className="service-area-box__top">
              <span>NYC</span>
              <strong>Plumber</strong>
            </div>
            <dl>
              <div>
                <dt>Business name</dt>
                <dd>A&amp;E NYC Plumbing</dd>
              </div>
              <div>
                <dt>Listed address</dt>
                <dd>{address}</dd>
              </div>
              <div>
                <dt>Phone</dt>
                <dd>
                  <a href={phoneHref}>{phoneDisplay}</a>
                </dd>
              </div>
              <div>
                <dt>Website</dt>
                <dd>
                  <a href={website} target="_blank" rel="noreferrer">
                    {website.replace(/^https?:\/\//, "").replace(/\/$/, "")}
                  </a>
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </section>

      <section className="faq-section" aria-label="Frequently asked questions">
        <div className="site-shell faq-grid">
          <div className="section-heading">
            <p className="section-kicker">Current details</p>
            <h2>Call for anything not listed in the source data.</h2>
          </div>
          <div className="faq-list">
            {faqs.map((faq) => (
              <details key={faq.question}>
                <summary>{faq.question}</summary>
                <p>{faq.answer}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      <section className="contact-section" id="contact">
        <div className="site-shell contact-grid">
          <div>
            <p className="section-kicker">Contact A&amp;E NYC Plumbing</p>
            <h2>Ready to make the call?</h2>
            <p>
              Use the listed number for plumbing requests, scheduling
              questions, and current information. If you need details that are
              not shown here, ask during the call.
            </p>
          </div>
          <div className="contact-actions">
            <a className="button button--primary button--large" href={phoneHref}>
              Call {phoneDisplay}
            </a>
            <a
              className="button button--secondary button--large"
              href={website}
              target="_blank"
              rel="noreferrer"
            >
              Visit Original Site
            </a>
          </div>
        </div>
      </section>

      <footer className="site-footer">
        <div className="site-shell footer-grid">
          <div>
            <strong>A&amp;E NYC Plumbing</strong>
            <p>Plumber in New York City</p>
          </div>
          <address>
            <a href={phoneHref}>{phoneDisplay}</a>
            <span>{address}</span>
            <a href={website} target="_blank" rel="noreferrer">
              {website.replace(/^https?:\/\//, "").replace(/\/$/, "")}
            </a>
          </address>
        </div>
      </footer>
    </main>
  );
}
