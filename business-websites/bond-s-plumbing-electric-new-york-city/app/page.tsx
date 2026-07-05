import business from "../business.json";

type BusinessData = {
  name: string;
  category?: string | null;
  businessType?: string | null;
  designStyle?: string | null;
  designDirection?: string | null;
  city?: string | null;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  originalWebsite?: string | null;
  headline?: string | null;
  subheadline?: string | null;
  services?: string[];
  cta?: string | null;
  searchKeyword?: string | null;
  searchLocation?: string | null;
};

const data = business as BusinessData;

function clean(value?: string | null) {
  return value?.trim() || "";
}

function textBlob() {
  return [data.name, data.category, data.businessType, data.searchKeyword, data.designStyle]
    .map((item) => clean(item).toLowerCase())
    .join(" ");
}

function sector() {
  const text = textBlob();
  if (/plumb|drain|sewer|water heater|electric|hvac|roof|contractor|construction|repair|locksmith|pest|cleaning|garage/.test(text)) return "service";
  if (/dent|clinic|medical|orthodont|chiro|physio|therapy/.test(text)) return "clinic";
  if (/restaurant|cafe|coffee|bakery|pizza|bar|grill|sushi|ramen|food/.test(text)) return "hospitality";
  if (/salon|spa|barber|hair|nail|beauty/.test(text)) return "lifestyle";
  if (/gym|fitness|pilates|yoga|trainer/.test(text)) return "fitness";
  return "professional";
}

function sectorLabel() {
  const s = sector();
  if (s === "service") return "Local service response";
  if (s === "clinic") return "Care, trust, and appointments";
  if (s === "hospitality") return "Menu, location, and ordering";
  if (s === "lifestyle") return "Bookings, services, and style";
  if (s === "fitness") return "Programs, training, and membership";
  return "Local business growth";
}

function primaryAction() {
  if (data.cta) return data.cta;
  if (sector() === "clinic") return "Book an appointment";
  if (sector() === "hospitality") return "Call for current availability";
  if (sector() === "lifestyle") return "Book a visit";
  if (sector() === "fitness") return "Ask about programs";
  if (sector() === "service") return "Call for service";
  return "Contact us";
}

function defaultServices() {
  const s = sector();
  if (s === "service") return ["Urgent service calls", "Inspection and troubleshooting", "Repair and installation", "Local residential support"];
  if (s === "clinic") return ["New patient inquiries", "Preventive care", "Emergency or urgent appointments", "Clear location and contact flow"];
  if (s === "hospitality") return ["Menu and ordering questions", "Dine-in and takeout details", "Groups and special requests", "Directions and current hours"];
  if (s === "lifestyle") return ["Appointments", "Signature services", "Consultation and pricing questions", "Location and contact"];
  if (s === "fitness") return ["Classes or training", "Membership questions", "Schedule inquiries", "Getting started"];
  return ["Core services", "Customer inquiries", "Location and contact", "Fast mobile experience"];
}

function trustPoints() {
  const s = sector();
  if (s === "service") return ["Fast phone-first flow", "Clear service categories", "Built around local search intent"];
  if (s === "clinic") return ["Calm appointment path", "Trust-building service structure", "Easy contact and directions"];
  if (s === "hospitality") return ["Quick menu/order path", "Mobile-friendly directions", "Simple contact flow"];
  if (s === "lifestyle") return ["Service-led booking flow", "Polished presentation", "Easy call or email actions"];
  if (s === "fitness") return ["Program discovery", "Strong CTA flow", "Mobile-first membership inquiry"];
  return ["Clear value proposition", "Direct contact flow", "Local credibility structure"];
}

function processSteps() {
  const s = sector();
  if (s === "service") return ["Call with the issue", "Confirm the location", "Schedule the service visit"];
  if (s === "clinic") return ["Choose the care need", "Call or email the office", "Book the next available visit"];
  if (s === "hospitality") return ["Check the offering", "Call for current hours", "Visit, order, or reserve"];
  if (s === "lifestyle") return ["Review services", "Call or email to book", "Arrive for the appointment"];
  if (s === "fitness") return ["Pick a program", "Ask about schedule", "Start training"];
  return ["Review services", "Contact the team", "Confirm next steps"];
}

function siteToneClass() {
  const style = clean(data.designStyle) || sector();
  return style.replace(/[^a-z0-9_-]+/gi, "-").toLowerCase();
}

const services = data.services?.length ? data.services : defaultServices();
const city = clean(data.city || data.searchLocation);
const address = clean(data.address);
const businessType = clean(data.businessType || data.category || data.searchKeyword) || "local business";
const headline = clean(data.headline) || `${data.name} — ${businessType}${city ? ` in ${city}` : ""}`;
const subheadline = clean(data.subheadline) || `A fast, clear, mobile-first website built around how customers actually contact ${data.name}.`;

export default function HomePage() {
  return (
    <main className={`site ${sector()} ${siteToneClass()}`}>
      <header className="navShell" aria-label="Site header">
        <a className="brandMark" href="#top" aria-label={data.name}>{data.name}</a>
        <nav className="navLinks" aria-label="Page sections">
          <a href="#services">Services</a>
          <a href="#why">Why us</a>
          <a href="#contact">Contact</a>
        </nav>
        {data.phone ? <a className="navCta" href={`tel:${data.phone}`}>{data.phone}</a> : <a className="navCta" href="#contact">Contact</a>}
      </header>

      <section id="top" className="heroShell">
        <div className="heroCopy">
          <p className="eyebrow">{sectorLabel()}</p>
          <h1>{headline}</h1>
          <p className="subtitle">{subheadline}</p>
          <div className="ctaRow">
            {data.phone && <a className="button primary" href={`tel:${data.phone}`}>{primaryAction()}</a>}
            {data.email && <a className="button secondary" href={`mailto:${data.email}`}>Email {data.name}</a>}
            {!data.phone && !data.email && <a className="button primary" href="#contact">Contact {data.name}</a>}
          </div>
          <div className="heroMeta" aria-label="Business details">
            <span>{businessType}</span>
            {city && <span>{city}</span>}
            {address && <span>{address}</span>}
          </div>
        </div>

        <aside className="heroCard" aria-label="Contact card">
          <div>
            <p className="cardLabel">Ready to act?</p>
            <h2>{primaryAction()}</h2>
          </div>
          <div className="contactStack">
            {data.phone && <a className="contactLine strong" href={`tel:${data.phone}`}>{data.phone}</a>}
            {data.email && <a className="contactLine" href={`mailto:${data.email}`}>{data.email}</a>}
            {data.originalWebsite && <a className="contactLine" href={data.originalWebsite}>Original website</a>}
            {!data.phone && !data.email && <span className="contactLine">Use the contact details below.</span>}
          </div>
        </aside>
      </section>

      <section id="why" className="trustBand" aria-label="Trust points">
        {trustPoints().map((point) => (
          <div className="trustItem" key={point}>
            <span aria-hidden="true">●</span>
            <strong>{point}</strong>
          </div>
        ))}
      </section>

      <section id="services" className="sectionShell sectionSplit">
        <div className="sectionIntro">
          <p className="eyebrow">Services</p>
          <h2>Built around what customers need before they contact you.</h2>
          <p>{clean(data.designDirection) || `The layout prioritizes ${businessType}, contact clarity, local trust, and fast mobile decisions.`}</p>
        </div>
        <div className="serviceGrid">
          {services.slice(0, 6).map((service, index) => (
            <article className="serviceCard" key={service}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <h3>{service}</h3>
              <p>{sector() === "service" ? "Clear, direct copy helps urgent visitors understand the next step." : "Focused section copy helps visitors decide quickly and contact with confidence."}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="sectionShell processShell">
        <div className="sectionIntro compact">
          <p className="eyebrow">Next step</p>
          <h2>A simple path from search to contact.</h2>
        </div>
        <div className="processGrid">
          {processSteps().map((step, index) => (
            <article className="processCard" key={step}>
              <span>Step {index + 1}</span>
              <h3>{step}</h3>
            </article>
          ))}
        </div>
      </section>

      <section id="contact" className="contactShell">
        <div>
          <p className="eyebrow">Contact</p>
          <h2>{data.name}</h2>
          <p>{address || city || "Call or email for current location details."}</p>
        </div>
        <div className="contactActions">
          {data.phone && <a className="button primary" href={`tel:${data.phone}`}>{data.phone}</a>}
          {data.email && <a className="button secondary" href={`mailto:${data.email}`}>{data.email}</a>}
          {data.originalWebsite && <a className="button secondary" href={data.originalWebsite}>Visit original site</a>}
        </div>
      </section>

      <footer className="footerShell">
        <span>{data.name}</span>
        <span>{businessType}{city ? ` · ${city}` : ""}</span>
      </footer>
    </main>
  );
}
