import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, FileDown } from 'lucide-react';
import { clientApi } from '../../services/dashboard';
import { ReportCard } from '../../components/dashboard/ReportShared';

export default function ClientReportDetail() {
  const { id } = useParams();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [pdfBusy, setPdfBusy] = useState(false);
  const [pdfError, setPdfError] = useState(null);

  useEffect(() => {
    clientApi.reports().then((rs) => {
      setReport(rs.find((r) => r.id === id) || null);
      setLoading(false);
    });
  }, [id]);

  const onDownloadPdf = async () => {
    setPdfBusy(true);
    setPdfError(null);
    try {
      await clientApi.downloadReportPdf(id);
    } catch (e) {
      setPdfError(e?.message || 'Could not generate the PDF.');
    } finally { setPdfBusy(false); }
  };

  if (loading) return <p className="text-sm text-musper-muted">Loading…</p>;

  if (!report) {
    return (
      <div className="space-y-8">
        <Link to="/dashboard/reports" className="inline-flex items-center gap-1.5 text-sm text-musper-green hover:text-musper-green-deep">
          <ArrowLeft size={14} /> Back to reports
        </Link>
        <p className="text-sm text-musper-muted">Report not found, or no longer shared with you.</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <Link to="/dashboard/reports" className="inline-flex items-center gap-1.5 text-sm text-musper-green hover:text-musper-green-deep">
          <ArrowLeft size={14} /> Back to reports
        </Link>
        <button
          type="button"
          onClick={onDownloadPdf}
          disabled={pdfBusy}
          className="inline-flex items-center gap-2 rounded-full border border-musper-line bg-musper-cream-soft px-4 py-2 text-sm font-medium text-musper-ink/80 transition hover:border-musper-green/30 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <FileDown size={14} /> {pdfBusy ? 'Generating PDF…' : 'Download PDF'}
        </button>
      </div>

      {pdfError && (
        <div className="rounded-2xl border border-musper-orange/30 bg-musper-orange-soft px-4 py-3 text-sm text-musper-orange-dark">
          {pdfError}
        </div>
      )}

      <ReportCard report={report} />
    </div>
  );
}
