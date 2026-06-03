import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, FileDown } from 'lucide-react';
import { clientApi } from '../../services/dashboard';
import { ReportCard } from '../../components/dashboard/ReportShared';

export default function ClientReportDetail() {
  const { id } = useParams();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    clientApi.reports().then((rs) => {
      setReport(rs.find((r) => r.id === id) || null);
      setLoading(false);
    });
  }, [id]);

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
          className="inline-flex items-center gap-2 rounded-full border border-musper-line bg-musper-cream-soft px-4 py-2 text-sm font-medium text-musper-ink/80 transition hover:border-musper-green/30"
          title="PDF download coming in a later phase"
        >
          <FileDown size={14} /> Download PDF
        </button>
      </div>
      <ReportCard report={report} />
    </div>
  );
}
