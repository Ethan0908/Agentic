import business from "../business.json";

export default function HomePage() {
  const designStyle = business.designStyle || "professional-local";

  return (
    <main className={`site ${designStyle}`}>
      <section className="hero">
        <div className="heroText">
          <p className="eyebrow">{business.businessType || business.category}</p>
          <h1>{business.headline}</h1>
          <p className="subtitle">{business.subheadline}</p>
          <div className="ctaRow">
            {business.phone && <a className="button" href={`tel:${business.phone}`}>Call now</a>}
            {business.email && <a className="button ghost" href={`mailto:${business.email}`}>Email us</a>}
            {business.originalWebsite && <a className="button ghost" href={business.originalWebsite}>Original site</a>}
          </div>
        </div>
        <div className="card">
          <span>{business.category}</span>
          <strong>{business.name}</strong>
          <p>{business.city}</p>
          {business.phone && <a className="phoneLarge" href={`tel:${business.phone}`}>{business.phone}</a>}
        </div>
      </section>

      <section className="section split">
        <div>
          <p className="eyebrow">What this site should sell</p>
          <h2>{business.designDirection || "Built for customers who are already searching."}</h2>
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
          <p>{business.address || business.city}</p>
          {!business.address && <p>Call for current location details.</p>}
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
