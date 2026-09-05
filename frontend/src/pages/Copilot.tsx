import { useState } from 'react';
import { Send, Loader2, Copy, Check } from 'lucide-react';
import { api } from '../lib/api';
import { formatCurrency, formatNumber, cn } from '../lib/utils';

interface CopilotResponse {
  answer: string;
  evidence?: string;
  calculation?: string;
  recommendation?: string;
  assumptions?: string;
  error?: string;
}

const SUGGESTED_QUESTIONS = [
  "What's running out?",
  "What's overstocked?",
  "How did laptops perform this month?",
  "Which store performed best?",
  "What should I reorder today?",
  "Which products had sales drops?",
  "Compare Hyderabad and Vijayawada",
  "Why is Wireless Mouse high priority?",
  "What will sales be next year?",
];

export function Copilot() {
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState<CopilotResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<Array<{ question: string; response: CopilotResponse }>>([]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || loading) return;

    setLoading(true);
    try {
      const result = await api.copilot(question);
      setResponse(result);
      setHistory(prev => [{ question, response: result }, ...prev].slice(0, 10));
    } catch (err) {
      setResponse({
        answer: 'Error communicating with the copilot',
        error: 'Network error',
        evidence: '',
        calculation: '',
        recommendation: '',
        assumptions: '',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestedClick = (q: string) => {
    setQuestion(q);
    handleSubmit(new Event('submit') as unknown as React.FormEvent);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="space-y-8 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">AI Copilot</h1>
        <p className="text-gray-500 mt-1">Ask questions about your inventory and sales in plain language</p>
      </div>

      <form onSubmit={handleSubmit} className="card">
        <div className="flex gap-3">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask me anything about your inventory, sales, or recommendations..."
            className="flex-1 input"
            disabled={loading}
            aria-label="Copilot question"
          />
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="btn-primary px-6 disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin mr-2" />
                Thinking...
              </>
            ) : (
              <>
                <Send className="w-5 h-5 mr-2" />
                Ask
              </>
            )}
          </button>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          {SUGGESTED_QUESTIONS.map((q) => (
            <button
              key={q}
              type="button"
              onClick={() => handleSuggestedClick(q)}
              disabled={loading}
              className="text-sm px-3 py-1.5 bg-gray-50 hover:bg-gray-100 text-gray-700 rounded-lg border border-gray-200 transition-colors disabled:opacity-50"
            >
              {q}
            </button>
          ))}
        </div>
      </form>

      {response && (
        <div className="space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              Answer
              {response.error && (
                <span className="badge badge-critical">{response.error}</span>
              )}
            </h2>
            <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap">
              {response.answer}
            </div>
          </div>

          {response.evidence && (
            <div className="card border-l-4 border-indigo-500">
              <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                Evidence
                <button
                  onClick={() => copyToClipboard(response.evidence!)}
                  className="ml-auto text-sm text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
                >
                  <Copy className="w-4 h-4" />
                  Copy
                </button>
              </h3>
              <pre className="bg-gray-50 p-4 rounded-lg text-sm overflow-x-auto text-gray-700">
                {response.evidence}
              </pre>
            </div>
          )}

          {response.calculation && (
            <div className="card border-l-4 border-green-500">
              <h3 className="font-medium text-gray-900 mb-3">Calculation</h3>
              <pre className="bg-gray-50 p-4 rounded-lg text-sm overflow-x-auto text-gray-700 font-mono">
                {response.calculation}
              </pre>
            </div>
          )}

          {response.recommendation && (
            <div className="card border-l-4 border-orange-500">
              <h3 className="font-medium text-gray-900 mb-3">Recommendation</h3>
              <div className="prose prose-sm max-w-none text-gray-700">
                {response.recommendation}
              </div>
            </div>
          )}

          {response.assumptions && (
            <div className="card border-l-4 border-gray-500">
              <h3 className="font-medium text-gray-900 mb-3">Assumptions</h3>
              <div className="prose prose-sm max-w-none text-gray-600">
                {response.assumptions}
              </div>
            </div>
          )}
        </div>
      )}

      {history.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Questions</h2>
          <div className="space-y-3">
            {history.map((item, index) => (
              <div key={index} className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                onClick={() => {
                  setQuestion(item.question);
                  setResponse(item.response);
                }}>
                <p className="text-sm font-medium text-gray-900">{item.question}</p>
                <p className="text-xs text-gray-500 mt-1 line-clamp-1">{item.response.answer}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}