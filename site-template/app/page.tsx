import business from "../business.json";

export default function HomePage() {
  return (
    <main>
      <section className="hero">
        <div className="heroText">
          <p className="eyebrow">{business.category}</p>
          <h1>{business.headline}</h1>
          <p className="subtitle">{business.subheadline}</p>
          <div className="ctaRow">
            {business.phone && <a className="button" href={`tel:${business.phone}`}>Call now</a>}
            {business.email && <a className="button ghost" href={`mailto:${business.email}`}>Email us</a>}
          </div>
        </div>
        <div className="card">
          <span>Website preview</span>
          <strong>{business.name}</strong>
          <p>{business.city}</p>
        </div>
      </section>

      <section className="section split">
        <div>
          <p className="eyebrow">Services</p>
          <h2>Built for customers who are already searching.</h2>
        </div>
        <div className="serviceGrid">
          {business.services.map((service) => (
            <div className="service" key={service}>{service}</div>
          ))}
        </div>
      </section>

      <section className="section contact">
        <div>
          <p className="eyebrow">Contact</p>
          <h2>{business.cta}</h2>
          <p>{business.address}</p>
        </div>
        <div className="contactLinks">
          {business.phone && <a href={`tel:${business.phone}`}>{business.phone}</a>}
          {business.email && <a href={`mailto:${business.email}`}>{business.email}</a>}
          {business.originalWebsite && <a href={business.originalWebsite}>Original website</a>}
        </div>
      </section>
    </main>
  );
}
