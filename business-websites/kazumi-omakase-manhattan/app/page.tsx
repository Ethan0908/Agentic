import type { CSSProperties } from 'react';
import business from '../data/business.json';
import design from '../data/design.json';
import sections from '../data/sections.json';

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

function themeVars(): CSSProperties {
  return {
    '--bg': design.tokens.bg,
    '--ink': design.tokens.ink,
    '--muted': design.tokens.muted,
    '--surface': design.tokens.surface,
    '--surface-strong': design.tokens.surfaceStrong,
    '--accent': design.tokens.accent,
    '--accent-dark': design.tokens.accentDark,
  } as CSSProperties;
}

function panelTitle() {
  if (sections.intent.emergency) return 'Built for fast decisions.';
  if (sections.intent.professional) return 'Built around confidence.';
  if (sections.intent.appointment) return 'Built around a clear appointment path.';
  return 'Built around a clear next step.';
}

function panelTopline() {
  if (sections.intent.emergency) return 'Priority contact path';
  if (sections.intent.professional) return 'Decision confidence';
  if (sections.intent.appointment) return 'Appointment flow';
  return 'Premium service flow';
}

function processLabels() {
  if (sections.processVariant === 'rapid-response') {
    return [
      ['01', 'Contact', 'Make the request with location, timing, and the problem.'],
      ['02', 'Assess', 'The issue is scoped so the next step is clear.'],
      ['03', 'Act', 'The work moves forward with direct communication.'],
    ];
  }
  if (sections.processVariant === 'consultative') {
    return [
      ['01', 'Discovery', 'Share goals, constraints, and relevant details.'],
      ['02', 'Recommendation', 'Get a practical path based on what matters most.'],
      ['03', 'Next step', 'Move into booking, quote, or consultation with clarity.'],
    ];
  }
  return [
    ['01', 'Scope', 'Project details are collected before the work is framed.'],
    ['02', 'Plan', 'You get the recommended quote path, visit, or action.'],
    ['03', 'Deliver', 'Work moves forward with calm, direct communication.'],
  ];
}

export default function Home() {
  const ctaHref = contactHref();
  const reviews = reviewList();
  const services = serviceList();

  return (
    <main style={themeVars()} data-theme={design.id} data-variant={sections.heroVariant}>
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
          <div className="panel-topline">{panelTopline()}</div>
          <h2>{panelTitle()}</h2>
          <div className="panel-grid">
            {processLabels().map(([number, title, description]) => (
              <div key={title}>
                <span>{number}</span>
                <strong>{title}</strong>
                <p>{description}</p>
              </div>
            ))}
          </div>
        </aside>
      </section>

      <section className={`proof-strip proof-${sections.proofVariant}`} aria-label="Business proof points">
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
            Clear sections help visitors understand what is offered, why it matters, and what to do next.
          </p>
        </div>
        <div className={`card-grid services-${sections.servicesVariant}`}>
          {services.map((service) => (
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
          <p className="eyebrow">Why it works</p>
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
            <p>The page uses supplied reviews or concrete process expectations instead of invented awards.</p>
          </article>
        </div>
      </section>

      <section id="process" className="section-pad process-section">
        <div className="section-intro narrow">
          <p className="eyebrow">Process</p>
          <h2>What happens after someone contacts {business.name}.</h2>
        </div>
        <div className={`timeline process-${sections.processVariant}`}>
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
              When proof is missing, the page should create confidence through process clarity, specific service details, and a clear contact path.
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

      <section id="contact" className={`final-cta section-pad final-${sections.finalCtaVariant}`}>
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
