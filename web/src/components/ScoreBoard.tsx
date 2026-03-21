interface Props {
  proTotal: number;
  conTotal: number;
  winner: string;
}

export default function ScoreBoard({ proTotal, conTotal, winner }: Props) {
  const total = proTotal + conTotal;
  const proPercent = total > 0 ? (proTotal / total) * 100 : 50;
  const conPercent = total > 0 ? (conTotal / total) * 100 : 50;
  const proWins = winner.toLowerCase().includes("pro") || winner.includes("正方");

  return (
    <div className="mb-6 animate-fade-in">
      <div className="flex items-center justify-between text-sm font-medium mb-2">
        <span className="text-pro">正方 {+proTotal.toFixed(1)}</span>
        <span className="text-con">反方 {+conTotal.toFixed(1)}</span>
      </div>
      <div className="flex h-3 rounded-full overflow-hidden">
        <div
          className="bg-pro transition-all duration-700"
          style={{ width: `${proPercent}%` }}
        />
        <div
          className="bg-con transition-all duration-700"
          style={{ width: `${conPercent}%` }}
        />
      </div>
      <div className="text-center mt-2">
        <span className="inline-block px-3 py-0.5 text-xs font-medium rounded-full bg-terracotta text-white">
          {proWins ? "正方胜" : "反方胜"}
        </span>
      </div>
    </div>
  );
}
