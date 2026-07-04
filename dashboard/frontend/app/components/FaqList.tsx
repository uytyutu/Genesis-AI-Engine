import { Card } from "./ui/Card";

export function FaqList({ items }: { items: { q: string; a: string }[] }) {
  return (
    <ul className="space-y-3" role="list">
      {items.map((item) => (
        <li key={item.q}>
          <Card hover={false} padding="md" as="article">
            <h3 className="font-medium text-genesis-text">{item.q}</h3>
            <p className="mt-2 text-sm leading-relaxed text-genesis-muted">{item.a}</p>
          </Card>
        </li>
      ))}
    </ul>
  );
}
