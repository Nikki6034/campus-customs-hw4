import { useEffect, useState } from "react";
import {
  getSizeGuide,
  getSizeRecommendation,
  type SizeChartRow,
  type SizeRecommendation,
} from "../api/client";

// Size guide + fit finder for the product page. Enter height and weight (metric
// or imperial) for a recommended size; the chart shows US/UK with chest in both
// inches and cm. onRecommend lets the page pre-select the suggested size.
export default function SizeFinder({
  onRecommend,
}: {
  onRecommend?: (size: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [chart, setChart] = useState<SizeChartRow[]>([]);
  const [units, setUnits] = useState<"metric" | "imperial">("imperial");
  const [height, setHeight] = useState("");
  const [weight, setWeight] = useState("");
  const [result, setResult] = useState<SizeRecommendation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (open && chart.length === 0) {
      getSizeGuide()
        .then(setChart)
        .catch(() => setChart([]));
    }
  }, [open, chart.length]);

  async function findSize(event: React.FormEvent) {
    event.preventDefault();
    const h = parseFloat(height);
    const w = parseFloat(weight);
    if (!(h > 0) || !(w > 0)) {
      setError("Enter a height and weight.");
      return;
    }
    setError(null);
    setBusy(true);
    try {
      const rec = await getSizeRecommendation(h, w, units);
      setResult(rec);
      onRecommend?.(rec.recommended_size);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't get a recommendation.");
    } finally {
      setBusy(false);
    }
  }

  const heightLabel = units === "metric" ? "Height (cm)" : "Height (in)";
  const weightLabel = units === "metric" ? "Weight (kg)" : "Weight (lb)";

  return (
    <div className="detail-block sizefinder">
      <button
        type="button"
        className="sizefinder-toggle"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        Size guide &amp; fit finder {open ? "–" : "+"}
      </button>

      {open && (
        <div className="sizefinder-body">
          <form className="sizefinder-form" onSubmit={findSize}>
            <div className="unit-toggle">
              <button
                type="button"
                className={units === "imperial" ? "unit active" : "unit"}
                onClick={() => setUnits("imperial")}
              >
                in / lb
              </button>
              <button
                type="button"
                className={units === "metric" ? "unit active" : "unit"}
                onClick={() => setUnits("metric")}
              >
                cm / kg
              </button>
            </div>
            <div className="sizefinder-inputs">
              <label>
                {heightLabel}
                <input
                  type="number"
                  inputMode="decimal"
                  value={height}
                  onChange={(e) => setHeight(e.target.value)}
                  min="0"
                />
              </label>
              <label>
                {weightLabel}
                <input
                  type="number"
                  inputMode="decimal"
                  value={weight}
                  onChange={(e) => setWeight(e.target.value)}
                  min="0"
                />
              </label>
              <button type="submit" className="btn btn-solid" disabled={busy}>
                {busy ? "…" : "Find my size"}
              </button>
            </div>
          </form>

          {error && <p className="sizefinder-error">{error}</p>}

          {result && (
            <div className="sizefinder-result">
              <p className="sizefinder-size">
                We'd start you in <strong>{result.recommended_size}</strong>
                <span className="sizefinder-usuk">
                  US {result.us} · UK {result.uk} · chest {result.chest_in} in /{" "}
                  {result.chest_cm} cm
                </span>
              </p>
              <p className="sizefinder-note">{result.note}</p>
            </div>
          )}

          {chart.length > 0 && (
            <table className="size-table">
              <thead>
                <tr>
                  <th>Size</th>
                  <th>US</th>
                  <th>UK</th>
                  <th>Chest (in)</th>
                  <th>Chest (cm)</th>
                </tr>
              </thead>
              <tbody>
                {chart.map((r) => (
                  <tr
                    key={r.size}
                    className={
                      result?.recommended_size === r.size ? "size-row active" : "size-row"
                    }
                  >
                    <td>{r.size}</td>
                    <td>{r.us}</td>
                    <td>{r.uk}</td>
                    <td>{r.chest_in}</td>
                    <td>{r.chest_cm}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
