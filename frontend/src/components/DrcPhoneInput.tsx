type Props = {
  value: string;
  onChange: (value: string) => void;
  className?: string;
  required?: boolean;
};

function DrcPhoneInput({ value, onChange, className = "", required = false }: Props) {
  return (
    <div className={`flex overflow-hidden rounded border bg-white ${className}`}>
      <span className="flex items-center border-r bg-slate-100 px-3 font-semibold text-slate-700">+243</span>
      <input
        className="min-w-0 flex-1 px-3 py-2 outline-none"
        inputMode="numeric"
        autoComplete="tel-national"
        pattern="[0-9]{9}"
        minLength={9}
        maxLength={9}
        placeholder="897970873"
        title="Saisissez les 9 chiffres sans zéro initial"
        value={value}
        onChange={(event) => onChange(event.target.value.replace(/\D/g, "").replace(/^0+/, "").slice(0, 9))}
        required={required}
      />
    </div>
  );
}

export default DrcPhoneInput;
