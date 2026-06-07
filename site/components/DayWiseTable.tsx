import { formatCrore, formatDate, type DayRow } from "../lib/data";

export function DayWiseTable({ rows }: { rows: DayRow[] }) {
  return (
    <div className="table-wrap">
      <table className="day-wise-table">
        <thead>
          <tr>
            <th>Day</th>
            <th>Date</th>
            <th>India nett</th>
            <th>Source and as-of</th>
            <th>Label</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.date}>
              <td>Day {row.day}</td>
              <td>{formatDate(row.date)}</td>
              <td className="num">{formatCrore(row.net_inr_cr.value)}</td>
              <td>
                {row.sources.map((source) => (
                  <span className="source-line" key={`${row.date}-${source.name}`}>
                    <a href={source.url}>{source.name}</a> as of {formatDate(source.as_of)}
                  </span>
                ))}
              </td>
              <td>{row.label}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
