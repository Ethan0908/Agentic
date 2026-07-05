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

function panelHeading() {
  if (sections.intent.emergency) return 'A direct path when the issue cannot wait.';
  if (sections.intent.professional) return 'A clearer way to choose your next step.';
  if (sections.intent.appointment) return 'A calm path from question to appointment.';
  return 'Clear scope, practical next steps, and careful follow-through.';
}

function panelLabel() {
  if (sections.intent.emergency) return 'Urgent request flow';
  if (sections.intent.professional) return 'Advisory flow';
  if (sections.intent.appointment) return 'Appointment flow';
  return 'Service flow';
}

function processLabels() {
  if (sections.processVariant === 'rapid-response') {
    return [
      ['01', 'Request', 'Share the location, timing, and the problem so the request can be understood quickly.'],
      ['02', 'Scope', 'The issue is reviewed and the practical next step is explained.'],
      ['03', 'Resolve', 'The work moves forward with clear communication and realistic expectations.'],
    ];
  }
  if (sections.processVariant === 'consultative') {
    return [
      ['01', 'Listen', 'Start with the goals, constraints, and details that affect the recommendation.'],
      ['02', 'Advise', 'Get a practical path based on what matters most for the situation.'],
      ['03', 'Move', 'Continue into a quote, booking, or consultation with fewer unknowns.'],
    ];
  }
  return [
    ['01', 'Share', 'Send the issue, location, and timing so the request can be scoped properly.'],
    ['02', 'Clarify', 'Receive a practical recommendation, quote path, or booking option.'],
    ['03', 'Complete', 'The job moves forward with direct communication from start to finish.'],
  ];
}

function actionSubtext() {
  if (business.phone) return `Call or request service across ${business.serviceArea}.`;
  if (business.email) return `Send details to ${business.email} and get the next step.`;
  return `Send a short request for ${business.businessType} in ${business.serviceArea}.`;
}

export default function Home() {
  const ctaHref = contactHref();
  const reviews = reviewList();
  const services = serviceList();
  const process = processLabels();

  return (
    <main style={themeVars()} data-theme={design.id} data-variant={sections.heroVariant}>
      <div className="page-shell">
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
            <a href="#standard">Standard</a>
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
            <p className="action-note">{actionSubtext()}</p>
          </div>

          <aside className="hero-panel" aria-label="Service summary">
            <div className="panel-kicker">{panelLabel()}</div>
            <h2>{panelHeading()}</h2>
            <div className="panel-divider" />
            <div className="panel-grid">
              {process.map(([number, title, description]) => (
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
              <span aria-hidden="true" />
              <p>{point}</p>
            </div>
          ))}
        </section>

        <section id="services" className="section-pad services-section">
          <div className="section-heading-row">
            <div>
              <p className="eyebrow">Services</p>
              <h2>Practical {business.businessType} support for {business.serviceArea}.</h2>
            </div>
            <p>
              Tell the team what is happening, where the work is needed, and the timing. The response can start with the right context instead of a long back-and-forth.
            </p>
          </div>

          <div className={`service-bento services-${sections.servicesVariant}`}>
            {services.map((service, index) => (
              <article className="service-card" key={service.title}>
                <div className="card-number">{String(index + 1).padStart(2, '0')}</div>
                <div>
                  <h3>{service.title}</h3>
                  <p>{service.description}</p>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section id="standard" className="section-pad standard-section">
          <div className="standard-main">
            <p className="eyebrow">Service standard</p>
            <h2>Clear communication before the work starts.</h2>
            <p>
              Good service is not only the final result. It is also how the request is handled, scoped, explained, and followed through. {business.name} keeps the experience focused on practical next steps.
            </p>
            <a className="text-link" href={ctaHref}>Start with a clear request →</a>
          </div>

          <div className="standard-list">
            <article>
              <span>01</span>
              <h3>Scope first</h3>
              <p>The request is understood before expectations are set.</p>
            </article>
            <article>
              <span>02</span>
              <h3>Straight answers</h3>
              <p>The next step is explained in plain language, whether that means a quote path, visit, booking, or recommendation.</p>
            </article>
            <article>
              <span>03</span>
              <h3>Local context</h3>
              <p>The service path stays connected to {business.serviceArea} and the work being requested.</p>
            </article>
          </div>
        </section>

        <section id="process" className="section-pad process-section">
          <div className="section-heading-row compact">
            <div>
              <p className="eyebrow">Process</p>
              <h2>From first request to a defined next step.</h2>
            </div>
            <p>
              A simple process helps visitors act without guessing what information to send or what happens after contact.
            </p>
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

        <section className="section-pad confidence-section">
          <div className="section-heading-row compact">
            <div>
              <p className="eyebrow">Confidence</p>
              <h2>{reviews.length ? 'What customers say.' : 'What customers can expect.'}</h2>
            </div>
            <p>
              Visitors get the information they need before choosing the next step.
            </p>
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
                Share the service needed, the location, preferred timing, and any photos or details that make the request easier to understand.
              </p>
            </div>
          )}
        </section>

        <section id="faq" className="section-pad faq-section">
          <div className="section-heading-row compact">
            <div>
              <p className="eyebrow">FAQ</p>
              <h2>Questions before getting started.</h2>
            </div>
            <p>
              Short answers reduce friction and help visitors decide whether to contact the business.
            </p>
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
          <div className="final-card">
            <p className="eyebrow">Next step</p>
            <h2>{business.offer}</h2>
            <p>{actionSubtext()}</p>
            <div className="hero-actions centred">
              <a className="button primary" href={ctaHref}>{business.primaryCta}</a>
              {business.phone ? <a className="button secondary" href={phoneHref(business.phone)}>Call {business.phone}</a> : null}
              {!business.phone && business.email ? <a className="button secondary" href={`mailto:${business.email}`}>{business.email}</a> : null}
            </div>
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
      </div>
    </main>
  );
}
