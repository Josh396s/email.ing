interface EmailProps {
  subject: string;
  sender: string;
  category: string;
  summary: string;
  urgency: string;
}

const urgencyColors: Record<string, string> = {
  "5": "border-l-red-500 bg-red-50",
  "4": "border-l-orange-500 bg-orange-50",
  "3": "border-l-yellow-500 bg-yellow-50",
  "2": "border-l-blue-500 bg-blue-50",
  "1": "border-l-gray-300 bg-white",
};

export default function EmailCard({ subject, sender, category, summary, urgency }: EmailProps) {
  return (
    <div className={`p-4 mb-3 border-l-4 rounded-r-lg shadow-sm transition-all hover:shadow-md ${urgencyColors[urgency] || "border-l-gray-200 bg-white"}`}>
      <div className="flex justify-between items-start mb-2">
        <span className="text-xs font-bold uppercase tracking-wider text-gray-500">{category}</span>
        <span className="text-xs font-mono px-2 py-1 bg-white border rounded">Urgency: {urgency}</span>
      </div>
      <h3 className="font-semibold text-gray-900 truncate">{subject}</h3>
      <p className="text-sm text-gray-600 mb-2 italic">from: {sender}</p>
      <div className="bg-white/50 p-2 rounded border border-gray-100">
        <p className="text-sm text-gray-800 leading-relaxed">
          <span className="font-bold text-indigo-600 mr-2">AI Summary:</span>
          {summary}
        </p>
      </div>
    </div>
  );
}