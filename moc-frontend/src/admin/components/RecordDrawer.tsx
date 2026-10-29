import { useEffect, useState } from "react";
import { ImagePlus } from "lucide-react";
import Drawer from "./Drawer";
import { inputCls, Toggle } from "./primitives";
import { cn } from "@/lib/utils";

export interface FieldDef<T> {
  key: keyof T & string;
  label: string;
  type: "text" | "password" | "number" | "textarea" | "select" | "toggle" | "datetime" | "image";
  options?: { value: string; label: string }[];
  required?: boolean;
  hint?: string;
  wide?: boolean;
}

interface RecordDrawerProps<T> {
  open: boolean;
  title: string;
  fields: FieldDef<T>[];
  initial: Partial<T>;
  saving: boolean;
  onClose: () => void;
  onSave: (values: Partial<T>) => void;
}

export default function RecordDrawer<T>({ open, title, fields, initial, saving, onClose, onSave }: RecordDrawerProps<T>) {
  const [values, setValues] = useState<Record<string, unknown>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (open) { setValues({ ...initial }); setErrors({}); }
  }, [open, initial]);

  const set = (key: string, v: unknown) => setValues((p) => ({ ...p, [key]: v }));

  const submit = () => {
    const next: Record<string, string> = {};
    for (const f of fields) {
      const v = values[f.key];
      if (f.required && (v === undefined || v === null || v === "")) next[f.key] = "Vui lòng nhập thông tin này";
    }
    setErrors(next);
    if (Object.keys(next).length === 0) onSave(values as Partial<T>);
  };

  const pickImage = (key: string, file?: File) => {
    if (!file) return;
    if (!/^image\/(jpeg|png|webp)$/.test(file.type)) return setErrors((e) => ({ ...e, [key]: "Chỉ nhận ảnh JPG, PNG hoặc WebP" }));
    if (file.size > 2 * 1024 * 1024) return setErrors((e) => ({ ...e, [key]: "Ảnh tối đa 2MB" }));
    const reader = new FileReader();
    reader.onload = () => { set(key, reader.result); setErrors((e) => ({ ...e, [key]: "" })); };
    reader.readAsDataURL(file);
  };

  return (
    <Drawer
      open={open} title={title} onClose={onClose}
      footer={<>
        <button onClick={onClose} className="btn btn-outline py-2.5! px-5! text-sm!">Huỷ</button>
        <button onClick={submit} disabled={saving} className="btn btn-primary py-2.5! px-6! text-sm! disabled:opacity-50">{saving ? "Đang lưu..." : "Lưu thay đổi"}</button>
      </>}
    >
      <div className="grid grid-cols-2 gap-x-4 gap-y-5">
        {fields.map((f) => {
          const v = values[f.key];
          const id = `field-${f.key}`;
          return (
            <div key={f.key} className={cn(f.wide || f.type === "textarea" || f.type === "image" ? "col-span-2" : "col-span-2 sm:col-span-1")}>
              {f.type === "toggle" ? (
                <div className="flex items-center justify-between gap-3 py-1">
                  <label htmlFor={id} className="text-sm font-medium">{f.label}</label>
                  <Toggle label={f.label} checked={!!v} onChange={(b) => set(f.key, b)} />
                </div>
              ) : (
                <>
                  <label htmlFor={id} className="text-[13px] font-semibold text-muted block mb-1.5">{f.label}{f.required && <span className="text-primary"> *</span>}</label>
                  {f.type === "textarea" && <textarea id={id} rows={5} value={String(v ?? "")} onChange={(e) => set(f.key, e.target.value)} className={cn(inputCls, "resize-none")} />}
                  {f.type === "select" && (
                    <select id={id} value={String(v ?? "")} onChange={(e) => set(f.key, e.target.value)} className={inputCls}>
                      <option value="" disabled>Chọn…</option>
                      {f.options?.map((o) => (<option key={o.value} value={o.value}>{o.label}</option>))}
                    </select>
                  )}
                  {(f.type === "text" || f.type === "password" || f.type === "number" || f.type === "datetime") && (
                    <input
                      id={id} className={inputCls}
                      type={f.type === "datetime" ? "datetime-local" : f.type}
                      value={String(v ?? "")}
                      onChange={(e) => set(f.key, f.type === "number" ? (e.target.value === "" ? "" : Number(e.target.value)) : e.target.value)}
                    />
                  )}
                  {f.type === "image" && (
                    <label htmlFor={id} className="flex items-center justify-center h-36 rounded-xl border-[1.5px] border-dashed border-black/20 bg-white cursor-pointer overflow-hidden hover:border-primary">
                      {typeof v === "string" && v ? <img src={v} alt="Ảnh xem trước" className="w-full h-full object-cover" /> : (
                        <span className="flex flex-col items-center gap-1.5 text-sm text-muted"><ImagePlus width={22} height={22} />Chọn ảnh (JPG, PNG, WebP · tối đa 2MB)</span>
                      )}
                      <input id={id} type="file" accept="image/jpeg,image/png,image/webp" className="sr-only" onChange={(e) => pickImage(f.key, e.target.files?.[0])} />
                    </label>
                  )}
                </>
              )}
              {f.hint && <p className="text-xs text-muted mt-1.5">{f.hint}</p>}
              {errors[f.key] && <p className="text-xs text-primary mt-1.5">{errors[f.key]}</p>}
            </div>
          );
        })}
      </div>
    </Drawer>
  );
}
