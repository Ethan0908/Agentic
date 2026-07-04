import business from "../business.json";

const courses = [
  ["01", "Hokkaido scallop", "Yuzu kosho, sea salt, young shiso"],
  ["02", "Aged bluefin akami", "House nikiri, toasted nori"],
  ["03", "Santa Barbara uni", "Warm rice, wasabi, citrus zest"],
  ["04", "Kinmedai", "Binchotan kiss, plum vinegar"],
  ["05", "Anago finale", "Charcoal glaze, sansho, sesame"]
];

const details = [
  "12-seat hinoki counter",
  "Two seatings nightly",
  "Seasonal Edomae progression",
  "Sake and tea pairings"
];

const schedule = [
  ["Tuesday - Thursday", "6:00 PM and 8:45 PM"],
  ["Friday - Saturday", "5:30 PM and 8:30 PM"],
  ["Sunday - Monday", "Private events only"]
];

export default function HomePage() {
  return (
    <main>
      <nav className="nav" aria-label="Primary navigation">
        <a className="brand" href="#top" aria-label={`${business.name} home`}>
          <span>K</span>
          {business.name}
        </a>
        <div className="navLinks">
          <a href="#menu">Menu</a>
          <a href="#experience">Experience</a>
          <a href="#reserve">Reserve</a>
        </div>
      </nav>

      <section className="hero" id="top">
        <div className="heroCopy">
          <p className="eyebrow">{business.category} / {business.city}</p>
          <h1>{business.headline}</h1>
          <p className="subtitle">{business.subheadline}</p>
          <div className="ctaRow">
            {business.phone && <a className="button" href={`tel:${business.phone}`}>Reserve by phone</a>}
            {business.email && <a className="button ghost" href={`mailto:${business.email}`}>Private dining</a>}
          </div>
        </div>

        <aside className="heroCard" aria-label="Restaurant details">
          <div className="moon" />
          <p>Tonight&apos;s Counter</p>
          <strong>18 courses</strong>
          <span>Market-led omakase served over two quiet hours in NoMad.</span>
        </aside>
      </section>

      <section className="marquee" aria-label="Restaurant highlights">
        {details.map((detail) => (
          <span key={detail}>{detail}</span>
        ))}
      </section>

      <section className="section intro" id="experience">
        <div>
          <p className="eyebrow">The Room</p>
          <h2>A quiet counter built around knife work, warm rice, and exact timing.</h2>
        </div>
        <p>
          Kura NoMad is an intimate New York City omakase restaurant where each seat
          faces the chef. The menu changes with the morning market, moving from
          chilled otsumami to precise nigiri and a restrained seasonal dessert.
        </p>
      </section>

      <section className="section menuSection" id="menu">
        <div className="sectionHeader">
          <p className="eyebrow">Sample Progression</p>
          <h2>Tonight may move like this.</h2>
        </div>

        <div className="courseList">
          {courses.map(([number, name, description]) => (
            <article className="course" key={name}>
              <span>{number}</span>
              <div>
                <h3>{name}</h3>
                <p>{description}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="section split">
        <div className="imagePanel">
          <span>12</span>
        </div>
        <div className="quotePanel">
          <p className="eyebrow">Philosophy</p>
          <blockquote>
            Nothing excessive. Fish at its peak, rice at body temperature, and a
            room calm enough to notice both.
          </blockquote>
        </div>
      </section>

      <section className="section reserve" id="reserve">
        <div>
          <p className="eyebrow">Reservations</p>
          <h2>{business.cta}</h2>
          <p>{business.address}</p>
        </div>
        <div className="reservationCard">
          {schedule.map(([day, time]) => (
            <div className="scheduleRow" key={day}>
              <span>{day}</span>
              <strong>{time}</strong>
            </div>
          ))}
          <div className="contactLinks">
            {business.phone && <a href={`tel:${business.phone}`}>{business.phone}</a>}
            {business.email && <a href={`mailto:${business.email}`}>{business.email}</a>}
          </div>
        </div>
      </section>
    </main>
  );
}
