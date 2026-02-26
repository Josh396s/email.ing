import { Briefcase, User, Newspaper, CreditCard, AlertTriangle, Mail } from 'lucide-react';

interface EmailRowProps {
  email: any;
  isSelected: boolean;
  onSelect: (email: any) => void;
}

// Map categories to specific icons and colors
const CATEGORY_MAP: Record<string, { icon: any, color: string, bgColor: string }> = {
  work: { icon: Briefcase, color: 'text-blue-600', bgColor: 'bg-blue-50' },
  personal: { icon: User, color: 'text-emerald-600', bgColor: 'bg-emerald-50' },
  newsletter: { icon: Newspaper, color: 'text-purple-600', bgColor: 'bg-purple-50' },
  transactional: { icon: CreditCard, color: 'text-amber-600', bgColor: 'bg-amber-50' },
  'safety warning': { icon: AlertTriangle, color: 'text-red-600', bgColor: 'bg-red-50' },
};

  // Dynamic priority styling based on the 1-5 urgency score
export const getPriorityStyles = (urgency: string) => {
    const level = parseInt(urgency);
    if (level == 1) return 'bg-blue-50 text-blue-600 border-blue-200';
    if (level == 2) return 'bg-green-50 text-green-600 border-green-200';
    if (level === 3) return 'bg-yellow-50 text-yellow-600 border-yellow-200';
    if (level == 4) return 'bg-orange-50 text-orange-600 border-orange-200';
    if (level >= 5) return 'bg-red-50 text-red-600 border-red-200';
    
    return 'bg-slate-50 text-slate-500 border-slate-200';
  };

export const EmailRow = ({ email, isSelected, onSelect }: EmailRowProps) => {
  const categoryKey = email.category?.toLowerCase();
  const categoryData = CATEGORY_MAP[categoryKey] || { icon: Mail, color: 'text-slate-400', bgColor: 'bg-slate-50' };
  const Icon = categoryData.icon;

  return (
    <div 
      onClick={() => onSelect(email)}
      className={`group flex items-center gap-4 p-5 border-b border-slate-50 cursor-pointer transition-all ${
        isSelected ? 'bg-indigo-50/50 border-l-4 border-l-indigo-600' : 'hover:bg-slate-50'
      }`}
    >
      <div className={`p-2 rounded-xl ${categoryData.bgColor} transition-transform group-hover:scale-110`}>
        <Icon className={categoryData.color} size={18} />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex justify-between items-center mb-1">
          <span className="text-[10px] font-bold text-slate-400 uppercase truncate max-w-[150px]">
            {email.sender}
          </span>
          <span className={`text-[9px] font-black px-1.5 py-0.5 rounded border uppercase tracking-wider ${getPriorityStyles(email.urgency)}`}>
            LVL {email.urgency}
          </span>
        </div>
        <h3 className="text-sm font-bold text-slate-800 truncate mb-0.5">{email.subject}</h3>
        <p className="text-xs text-slate-500 line-clamp-1 italic">"{email.summary}"</p>
      </div>
    </div>
  );
};