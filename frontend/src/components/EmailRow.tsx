import { Briefcase, User, Newspaper, CreditCard, AlertTriangle, Mail } from 'lucide-react';

interface EmailRowProps {
  email: any;
  isSelected: boolean;
  onSelect: (email: any) => void;
}

// Map categories to specific icons and colors
const CATEGORY_MAP: Record<string, { icon: any, color: string, bgColor: string }> = {
  work: { 
    icon: Briefcase, 
    color: 'text-[#F0EAD6]', 
    bgColor: 'bg-[#85B8BF]/80' 
  },
  personal: { 
    icon: User, 
    color: 'text-[#F0EAD6]', 
    bgColor: 'bg-[#85B8BF]/80' 
  },
  newsletter: { 
    icon: Newspaper, 
    color: 'text-[#F0EAD6]', 
    bgColor: 'bg-[#85B8BF]/80' 
  },
  transactional: { 
    icon: CreditCard, 
    color: 'text-[#F0EAD6]', 
    bgColor: 'bg-[#85B8BF]/80' 
  },
  'safety warning': { 
    icon: AlertTriangle, 
    color: 'text-[#F0EAD6]', 
    bgColor: 'bg-[#C25953]'
  },
};

  // Dynamic priority styling based on the 1-5 urgency score
export const getPriorityStyles = (urgency: string) => {
    const level = parseInt(urgency);
    if (level == 1) return 'bg-[#7C9EA6]/500 text-[#F0EAD6] border-[#7C9EA6]/50';
    if (level == 2) return 'bg-[#5E848C]/90 text-[#F0EAD6] border-[#5E848C]';
    if (level === 3) return 'bg-[#D66B5D]/75 text-[#F0EAD6] border-[#496B73]';
    if (level == 4) return 'bg-[#D66B5D]/170 text-[#F0EAD6] border-[#D66B5D]';
    if (level >= 5) return 'bg-[#C25953]/200 text-white border-[#C25953] shadow-lg';
    
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
        isSelected ? 'bg-indigo-50/50 border-l-4 border-l-indigo-600' : 'hover:bg-slate-50/50'
      }`}
    >
      <div className={`p-2 rounded-xl ${categoryData.bgColor} transition-transform group-hover:scale-110`}>
        <Icon className={categoryData.color} size={18} />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex justify-between items-center mb-1">
          <span className="text-[10px] font-bold text-[#F0EAD6]/80 uppercase truncate max-w-[250px]">
            {email.sender}
          </span>
          <span className={`text-[9px] font-black px-1.5 py-0.5 rounded border uppercase tracking-wider ${getPriorityStyles(email.urgency)}`}>
            LVL {email.urgency}
          </span>
        </div>
        <h3 className="text-[16px] font-bold text-[#F0EAD6] truncate mb-0.5">{email.subject}</h3>
        <p className="text-[14px] font-light text-[#F0EAD6]/80 line-clamp-1 italic">"{email.summary}"</p>
      </div>
    </div>
  );
};