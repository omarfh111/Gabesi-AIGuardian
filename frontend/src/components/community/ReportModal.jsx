import { FileText, MapPin, Send } from 'lucide-react';
import { Badge, Button, FormField, Input, Modal, Select, Textarea } from '../ui';
import { getIssueMeta, ISSUE_TYPES } from './issueMeta';

export default function ReportModal({
  isOpen,
  onClose,
  clickPos,
  form,
  setForm,
  onSubmit,
  loading,
}) {
  const selectedIssue = getIssueMeta(form.issue_type);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Submit an Environmental Report"
      description={
        clickPos
          ? `Location: ${clickPos.lat.toFixed(4)}, ${clickPos.lng.toFixed(4)}`
          : 'Choose a location on the map first.'
      }
      icon={<FileText className="h-4 w-4" />}
      size="sm"
    >
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="flex items-center gap-2">
          <Badge variant={selectedIssue.badgeVariant}>
            <selectedIssue.Icon className="mr-1 h-3.5 w-3.5" />
            {selectedIssue.label}
          </Badge>
          <Badge variant={form.severity === 'high' ? 'high' : form.severity === 'medium' ? 'medium' : 'low'}>
            {form.severity}
          </Badge>
        </div>

        <FormField label="Issue Type" htmlFor="issue_type">
          <Select
            id="issue_type"
            value={form.issue_type}
            onChange={(e) => setForm({ ...form, issue_type: e.target.value })}
          >
            {ISSUE_TYPES.map((type) => {
              const meta = getIssueMeta(type);
              return (
                <option key={type} value={type}>
                  {meta.label}
                </option>
              );
            })}
          </Select>
        </FormField>

        <FormField label="Severity" htmlFor="severity">
          <Select
            id="severity"
            value={form.severity}
            onChange={(e) => setForm({ ...form, severity: e.target.value })}
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </Select>
        </FormField>

        <FormField label="Description" htmlFor="description" meta="Optional, but useful for verification.">
          <Textarea
            id="description"
            rows={4}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            placeholder="Describe what happened, smell intensity, visible smoke, nearby landmarks..."
          />
        </FormField>

        <FormField
          label="Symptoms"
          htmlFor="symptoms"
          meta="Comma-separated, e.g. coughing, headache, nausea."
        >
          <Input
            id="symptoms"
            type="text"
            value={form.symptoms}
            onChange={(e) => setForm({ ...form, symptoms: e.target.value })}
            placeholder="coughing, headache"
          />
        </FormField>

        <div className="rounded-lg border border-gray-100 bg-gray-50 p-3 text-xs text-gray-600">
          <p className="mb-1 flex items-center gap-1">
            <MapPin className="h-3.5 w-3.5" />
            Privacy notice
          </p>
          <p>Your submitted location is rounded by the backend for anonymity.</p>
        </div>

        <div className="flex items-center justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" loading={loading} disabled={!clickPos}>
            <Send className="h-4 w-4" />
            Submit Report
          </Button>
        </div>
      </form>
    </Modal>
  );
}
