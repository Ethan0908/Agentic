import data from "../business.json";

const company = data.company;

export default function HomePage() {
  return (
    <main>
      <section>
        <p>Custom website starter</p>
        <h1>{company.name}</h1>
        <p>
          Codex should replace this starter page using business.json and
          GENERATION_PROMPT.md.
        </p>
        {company.phone && <a href={`tel:${company.phone}`}>Call</a>}
      </section>
    </main>
  );
}
