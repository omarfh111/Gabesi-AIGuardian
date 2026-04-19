import { useEffect, useState } from 'react';
import { Activity, Bolt, Brain, Leaf, PiggyBank, RefreshCw } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import EnergyDashboard from './EnergyDashboard';
import EnergyProfileForm from './EnergyProfileForm';
import { Badge, Button, Card, CardContent, CardHeader, CardTitle } from '../components/ui';

const API_BASE = '/api/v1/energy';

async function fetchUserData() {
  const res = await fetch(`${API_BASE}/user-data`);
  if (!res.ok) throw new Error('Failed to fetch user data');
  return res.json();
}

async function runParallelAnalysis(userData = null) {
  const res = await fetch(`${API_BASE}/analyse`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: userData ? JSON.stringify(userData) : '{}',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Analysis failed');
  }
  return res.json();
}

async function healthCheck() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('API unreachable');
  return res.json();
}

function formatAnalysis(text) {
  if (!text) return <span className="text-sm text-gray-500">No analysis available.</span>;
  return (
    <div className="prose prose-sm max-w-none prose-headings:text-slate-900 prose-p:text-slate-700 prose-strong:text-slate-900 prose-li:text-slate-700 prose-code:text-slate-800">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
    </div>
  );
}

function Energy() {
  const [page, setPage] = useState('home');
  const [userData, setUserData] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [apiStatus, setApiStatus] = useState('checking');
  const [langsmithStatus, setLangsmithStatus] = useState('off');

  useEffect(() => {
    async function init() {
      try {
        const health = await healthCheck();
        setApiStatus('ok');
        setLangsmithStatus(health.langsmith_tracing === 'true' ? 'on' : 'off');
        const data = await fetchUserData();
        setUserData(data);
      } catch {
        setApiStatus('error');
      }
    }
    init();
  }, []);

  const handleAnalyse = async (overriddenData = null) => {
    setLoading(true);
    setError(null);
    setResults(null);
    try {
      const data = await runParallelAnalysis(overriddenData || userData);
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFormSubmit = (data) => {
    setUserData(data);
    setPage('home');
    handleAnalyse(data);
  };

  if (page === 'form') {
    return (
      <div className="energy-page min-h-[calc(100vh-64px)] bg-gradient-to-br from-slate-50 via-white to-emerald-50 p-6">
        <EnergyProfileForm onBack={() => setPage('home')} onSubmit={handleFormSubmit} />
      </div>
    );
  }

  const initials = userData
    ? `${(userData.identite?.prenom || 'S')[0]}${(userData.identite?.nom || 'B')[0]}`
    : '??';

  return (
    <div className="energy-page min-h-[calc(100vh-64px)] bg-gradient-to-br from-slate-50 via-white to-emerald-50 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <Card className="rounded-xl">
          <CardHeader className="p-5">
            <CardTitle className="text-lg font-semibold text-gray-900">AI Energy Advisor</CardTitle>
            <p className="text-sm text-gray-600">4 agents analyze your environmental, energy, and financial profile.</p>
          </CardHeader>
          <CardContent className="flex flex-wrap items-center gap-2 px-5 pb-5 pt-0">
            <Badge variant={apiStatus === 'ok' ? 'low' : apiStatus === 'error' ? 'high' : 'medium'}>
              API {apiStatus}
            </Badge>
            <Badge variant={langsmithStatus === 'on' ? 'low' : 'neutral'}>LangSmith {langsmithStatus}</Badge>
            <Badge variant="neutral">GPT-4o-mini</Badge>
          </CardContent>
        </Card>

        {userData ? (
          <Card className="rounded-xl">
            <CardContent className="p-5">
              <div className="mb-4 flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-100 font-semibold text-emerald-700">
                  {initials}
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {userData.identite?.prenom} {userData.identite?.nom}
                  </p>
                  <p className="text-xs text-gray-500">
                    {userData.logement?.emplacement} - {userData.logement?.environement}
                  </p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                <div className="rounded-lg border border-gray-200 bg-gray-50 p-3">
                  <p className="text-xs text-gray-500">Salary</p>
                  <p className="text-sm font-medium text-gray-800">
                    {userData.identite?.salaire_tnd_accumule || userData.identite?.['salaire_tnd_accumulé']} TND
                  </p>
                </div>
                <div className="rounded-lg border border-gray-200 bg-gray-50 p-3">
                  <p className="text-xs text-gray-500">STEG bill</p>
                  <p className="text-sm font-medium text-gray-800">{userData.consommation?.avg_facture_steg_tnd} TND</p>
                </div>
                <div className="rounded-lg border border-gray-200 bg-gray-50 p-3">
                  <p className="text-xs text-gray-500">Consumption</p>
                  <p className="text-sm font-medium text-gray-800">{userData.consommation?.consommation_kwh_mensuelle} kWh</p>
                </div>
                <div className="rounded-lg border border-gray-200 bg-gray-50 p-3">
                  <p className="text-xs text-gray-500">CO2 estimate</p>
                  <p className="text-sm font-medium text-gray-800">{userData.consommation?.taux_co2_kg_par_an} kg/yr</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ) : null}

        {error ? (
          <Card className="rounded-xl border-red-200 bg-red-50">
            <CardContent className="p-4 text-sm text-red-700">{error}</CardContent>
          </Card>
        ) : null}

        <Card className="rounded-xl">
          <CardContent className="flex flex-wrap items-center gap-2 p-5">
            <Button onClick={() => handleAnalyse()} disabled={loading || apiStatus !== 'ok'}>
              {loading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Activity className="h-4 w-4" />}
              {loading ? 'Running analysis...' : 'Run analysis'}
            </Button>
            <Button variant="secondary" onClick={() => setPage('form')}>
              Update profile
            </Button>
            <p className="text-xs text-gray-500">Flow: ENV to Energy plus Finance to Expert synthesis</p>
          </CardContent>
        </Card>

        {loading ? (
          <Card className="rounded-xl">
            <CardContent className="flex items-center gap-2 p-5 text-sm text-gray-600">
              <RefreshCw className="h-4 w-4 animate-spin" />
              4 agents are executing...
            </CardContent>
          </Card>
        ) : null}

        {results ? (
          <>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
              <Card className="rounded-xl"><CardContent className="p-3"><p className="text-xs text-gray-500">Total</p><p className="text-sm font-medium">{results.total_time_seconds}s</p></CardContent></Card>
              <Card className="rounded-xl"><CardContent className="p-3"><p className="text-xs text-gray-500">ENV</p><p className="text-sm font-medium">{results.env_result.execution_time_seconds}s</p></CardContent></Card>
              <Card className="rounded-xl"><CardContent className="p-3"><p className="text-xs text-gray-500">Energy</p><p className="text-sm font-medium">{results.energie_result.execution_time_seconds}s</p></CardContent></Card>
              <Card className="rounded-xl"><CardContent className="p-3"><p className="text-xs text-gray-500">Finance</p><p className="text-sm font-medium">{results.finance_result.execution_time_seconds}s</p></CardContent></Card>
              <Card className="rounded-xl"><CardContent className="p-3"><p className="text-xs text-gray-500">Expert</p><p className="text-sm font-medium">{results.expert_result.execution_time_seconds}s</p></CardContent></Card>
            </div>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <Card className="rounded-xl">
                <CardHeader className="p-5 pb-2">
                  <CardTitle className="flex items-center gap-2 text-base font-medium"><Leaf className="h-4 w-4" /> Environment Agent</CardTitle>
                </CardHeader>
                <CardContent className="p-5 pt-2">{formatAnalysis(results.env_result.analysis)}</CardContent>
              </Card>
              <Card className="rounded-xl">
                <CardHeader className="p-5 pb-2">
                  <CardTitle className="flex items-center gap-2 text-base font-medium"><PiggyBank className="h-4 w-4" /> Finance Agent</CardTitle>
                </CardHeader>
                <CardContent className="p-5 pt-2">{formatAnalysis(results.finance_result.analysis)}</CardContent>
              </Card>
            </div>

            <Card className="rounded-xl">
              <CardHeader className="p-5 pb-2">
                <CardTitle className="flex items-center gap-2 text-base font-medium"><Bolt className="h-4 w-4" /> Renewable Energy Agent</CardTitle>
              </CardHeader>
              <CardContent className="p-5 pt-2">{formatAnalysis(results.energie_result.analysis)}</CardContent>
            </Card>

            <Card className="rounded-xl">
              <CardHeader className="p-5 pb-2">
                <CardTitle className="flex items-center gap-2 text-base font-medium"><Brain className="h-4 w-4" /> Expert Synthesis Agent</CardTitle>
              </CardHeader>
              <CardContent className="p-5 pt-2">{formatAnalysis(results.expert_result.analysis)}</CardContent>
            </Card>

            {results.dashboard ? <EnergyDashboard data={results.dashboard} /> : null}
          </>
        ) : null}
      </div>
    </div>
  );
}

export default Energy;
