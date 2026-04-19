import { Filter, SlidersHorizontal } from 'lucide-react';
import { Badge, Button, Card, CardContent, CardHeader, CardTitle } from '../ui';
import { getIssueMeta } from './issueMeta';

const SEVERITIES = ['', 'low', 'medium', 'high'];

export default function FiltersPanel({
  types,
  filterType,
  setFilterType,
  filterSeverity,
  setFilterSeverity,
  reportCount,
  isRefreshing,
}) {
  const hasActiveFilters = Boolean(filterType || filterSeverity);

  return (
    <div className="absolute bottom-6 left-4 z-10 w-[360px]">
      <Card className="rounded-xl bg-white/95 backdrop-blur">
        <CardHeader className="p-4 pb-3">
          <CardTitle className="flex items-center gap-2 text-base font-medium text-gray-900">
            <Filter className="h-4 w-4 text-gray-600" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 p-4 pt-0">
          <section>
            <div className="mb-2 flex items-center justify-between">
              <p className="text-xs text-gray-500">Issue type</p>
              {hasActiveFilters ? (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    setFilterType('');
                    setFilterSeverity('');
                  }}
                >
                  Clear filters
                </Button>
              ) : null}
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                variant={filterType === '' ? 'primary' : 'secondary'}
                size="sm"
                onClick={() => setFilterType('')}
              >
                All
              </Button>
              {types.map((type) => {
                const meta = getIssueMeta(type);
                return (
                  <Button
                    key={type}
                    variant={filterType === type ? 'primary' : 'secondary'}
                    size="sm"
                    onClick={() => setFilterType(type)}
                    className="capitalize"
                  >
                    <meta.Icon className="h-3.5 w-3.5" />
                    {meta.label}
                  </Button>
                );
              })}
            </div>
          </section>

          <section>
            <p className="mb-2 text-xs text-gray-500">Severity</p>
            <div className="grid grid-cols-4 gap-2">
              {SEVERITIES.map((severity) => (
                <Button
                  key={severity || 'all'}
                  variant={filterSeverity === severity ? 'primary' : 'secondary'}
                  size="sm"
                  onClick={() => setFilterSeverity(severity)}
                  className="capitalize"
                >
                  {severity || 'All'}
                </Button>
              ))}
            </div>
          </section>

          <div className="flex items-center justify-between rounded-lg bg-gray-50 p-2.5">
            <span className="text-xs text-gray-600">Current view</span>
            <Badge variant={hasActiveFilters ? 'medium' : 'neutral'} className="text-xs">
              <SlidersHorizontal className="mr-1 h-3 w-3" />
              {isRefreshing ? 'Updating...' : `${reportCount} reports`}
            </Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
