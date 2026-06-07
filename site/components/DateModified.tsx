import { formatDate } from "../lib/data";

export function DateModified({ value }: { value: string }) {
  return (
    <p className="date-modified">
      Updated <time dateTime={value}>{formatDate(value)}</time>
    </p>
  );
}
