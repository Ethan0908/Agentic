import business from '../data/business.json';

type Service = {
  title: string;
  description: string;
};

type Review = {
  quote?: string;
  text?: string;
  author?: string;
  name?: string;
  role?: string;
};

type Faq = {
  question: string;
  answer: string;
};

function phoneHref(phone?: string) {
  if (!phone) return '#contact';
  return `tel:${phone.replace(/[^+\d]/g, '')}`;
}

function contactHref() {
  if (business.phone) return phoneHref(business.phone);
  if (business.email) return `mailto:${business.email}`;
  return '#contact';
}

function serviceList(): Service[] {
  return business.services.length ? business.services : [];
}

function reviewList(): Review[] {
  return business.reviews || [];
}

function faqList(): Faq[] {
  return business.faqs || [];
}

export default function Home() {
  const ctaHref = contactHref();
  const reviews = reviewList();

  return (
    <main>
      <header className="site-header">
        <a className="brand" href="#top" aria-label={`${business.name} home`}>
          <span className="brand-mark" aria-hidden="true">{business.name.slice(0, 1)}</span>
          <span>
            <strong>{business.name}</strong>
            <small>{business.serviceArea}</small>
          </span>
        </a>
        <nav className="desktop-nav" aria-label="Main navigation">
          <a href="#services">Services</a>
          <a href="#process">Process</a>
          <a href="#faq">FAQ</a>
        </nav>
        <a className="header-cta" href={ctaHref}>{business.primaryCta}</a>
      </header>

      <section id="top" className="hero section-pad">
        <div className="hero-copy">
          <p className="eyebrow">{business.hero.eyebrow}</p>
          <h1>{business.hero.headline}</h1>
          <p className="hero-subhead">{business.hero.subheadline}</p>
          <div className="hero-actions">
            <a className="button primary" href={ctaHref}>{business.primaryCta}</a>
            <a className="button secondary" href="#services">{business.secondaryCta}</a>
          </div>
          <ul className="trust-list" aria-label="Key trust points">
            {business.proofPoints.slice(0, 3).map((point) => (
              <li key={point}>{point}</li>
            ))}
          </ul>
        </div>

        <aside className="hero-panel" aria-label="Service summary">
          <div className="panel-topline">Premium service flow</div>
          <h2>Built around a clear next step.</h2>
          <div className="panel-grid">
            <div>
              <span>01</span>
              <strong>Scope</strong>
              <p>Project details are collected before the work is framed.</p>
            </div>
            <div>
              <span>02</span>
              <strong>Plan</strong>
              <p>You get the recommended quote path, visit, or action.</p>
            </div>
            <div>
              <span>03</span>
              <strong>Deliver</strong>
              <p>Work moves forward with calm, direct communication.</p>
            </div>
          </div>
        </aside>
      </section>

      <section className="proof-strip" aria-label="Business proof points">
        {business.proofPoints.slice(0, 4).map((point) => (
          <div key={point}>
            <span>✓</span>
            <p>{point}</p>
          </div>
        ))}
      </section>

      <section id="services" className="section-pad split-section">
        <div className="section-intro">
          <p className="eyebrow">Services</p>
          <h2>Focused {business.businessType} help for real customer needs.</h2>
          <p>
            The page stays specific, simple, and action-oriented so visitors understand what to do next without reading a wall of text.
          </p>
        </div>
        <div className="card-grid">
          {serviceList().map((service) => (
            <article className="service-card" key={service.title}>
              <span aria-hidden="true" />
              <h3>{service.title}</h3>
              <p>{service.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section-pad decision-section">
        <div>
          <p className="eyebrow">Why it converts</p>
          <h2>Trust is built through clarity, not louder claims.</h2>
        </div>
        <div className="decision-grid">
          <article>
            <h3>Specific above the fold</h3>
            <p>Visitors see the service, area, CTA, and decision points immediately.</p>
          </article>
          <article>
            <h3>Short, scannable sections</h3>
            <p>Headings, cards, and bullets replace long paragraphs that people skip.</p>
          </article>
          <article>
            <h3>Proof without fake hype</h3>
            <p>The page uses provided reviews and concrete process promises instead of invented awards.</p>
          </article>
        </div>
      </section>

      <section id="process" className="section-pad process-section">
        <div className="section-intro narrow">
          <p className="eyebrow">Process</p>
          <h2>What happens after someone contacts {business.name}.</h2>
        </div>
        <div className="timeline">
          {business.processSteps.map((step, index) => (
            <article key={step.title}>
              <span>{String(index + 1).padStart(2, '0')}</span>
              <h3>{step.title}</h3>
              <p>{step.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section-pad proof-section">
        <div className="section-intro narrow">
          <p className="eyebrow">Confidence</p>
          <h2>{reviews.length ? 'What customers say.' : 'What customers can expect.'}</h2>
        </div>
        {reviews.length ? (
          <div className="review-grid">
            {reviews.slice(0, 3).map((review, index) => (
              <figure key={`${review.author || review.name || 'review'}-${index}`}>
                <blockquote>“{review.quote || review.text}”</blockquote>
                <figcaption>{review.author || review.name}{review.role ? `, ${review.role}` : ''}</figcaption>
              </figure>
            ))}
          </div>
        ) : (
          <div className="expectation-card">
            <h3>{business.guarantee}</h3>
            <p>
              Thin lead data should not create fake credibility. This template replaces missing reviews with clear expectations and a straightforward next step.
            </p>
          </div>
        )}
      </section>

      <section id="faq" className="section-pad faq-section">
        <div className="section-intro narrow">
          <p className="eyebrow">FAQ</p>
          <h2>Questions that help visitors decide faster.</h2>
        </div>
        <div className="faq-list">
          {faqList().map((item) => (
            <details key={item.question}>
              <summary>{item.question}</summary>
              <p>{item.answer}</p>
            </details>
          ))}
        </div>
      </section>

      <section id="contact" className="final-cta section-pad">
        <p className="eyebrow">Ready when you are</p>
        <h2>{business.offer}</h2>
        <p>Send the details once. Get a clear response about the right next step.</p>
        <div className="hero-actions centred">
          <a className="button primary" href={ctaHref}>{business.primaryCta}</a>
          {business.phone ? <a className="button secondary" href={phoneHref(business.phone)}>Call {business.phone}</a> : null}
          {!business.phone && business.email ? <a className="button secondary" href={`mailto:${business.email}`}>{business.email}</a> : null}
        </div>
      </section>

      <footer className="site-footer">
        <div>
          <strong>{business.name}</strong>
          <p>{business.businessType} serving {business.serviceArea}</p>
        </div>
        <a href={ctaHref}>{business.primaryCta}</a>
      </footer>

      <a className="mobile-sticky-cta" href={ctaHref}>{business.primaryCta}</a>
    </main>
  );
}
