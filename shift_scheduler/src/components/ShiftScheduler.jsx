import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
  Calendar, Users, Store, Download, Play, Settings, UserPlus, Trash2, X,
  Lock, Unlock, Upload, RotateCcw, Copy, Mail, ChevronUp, ChevronDown,
  Check, AlertTriangle, Link as LinkIcon, FileText,
} from 'lucide-react';

const VERSION = 'v1.3.0';
const DAYS = ['月曜日', '火曜日', '水曜日', '木曜日', '金曜日', '土曜日', '日曜日'];
const DAY_SHORT = ['月', '火', '水', '木', '金', '土', '日'];
const STORAGE_KEY = 'shiftSchedulerData';

// ───── Toast System ─────
const ToastContext = React.createContext(() => {});

const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);
  const idRef = useRef(0);

  const show = useCallback((message, type = 'info') => {
    const id = ++idRef.current;
    setToasts(t => [...t, { id, message, type }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 3500);
  }, []);

  return (
    <ToastContext.Provider value={show}>
      {children}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 items-end pointer-events-none">
        {toasts.map(t => (
          <div
            key={t.id}
            className="toast-enter bg-surface border border-strong rounded-lg px-4 py-3 min-w-[280px] shadow-2xl pointer-events-auto flex items-start gap-3"
            style={{ borderLeft: `3px solid var(--${t.type === 'error' ? 'danger' : t.type === 'success' ? 'success' : 'accent'})` }}
          >
            {t.type === 'error' && <AlertTriangle size={15} className="text-danger mt-0.5 flex-shrink-0" />}
            {t.type === 'success' && <Check size={15} className="text-success mt-0.5 flex-shrink-0" />}
            {t.type === 'info' && <div className="w-[15px] h-[15px] rounded-full bg-accent-dim border border-accent mt-0.5 flex-shrink-0" />}
            <div className="text-sm text-main whitespace-pre-line leading-relaxed">{t.message}</div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

const useToast = () => React.useContext(ToastContext);

// ───── Confirm Modal ─────
const ConfirmContext = React.createContext(() => Promise.resolve(false));

const ConfirmProvider = ({ children }) => {
  const [state, setState] = useState(null);
  const resolverRef = useRef(null);

  const confirm = useCallback((opts) => {
    return new Promise(resolve => {
      resolverRef.current = resolve;
      setState(typeof opts === 'string' ? { message: opts } : opts);
    });
  }, []);

  const close = (result) => {
    if (resolverRef.current) resolverRef.current(result);
    setState(null);
  };

  return (
    <ConfirmContext.Provider value={confirm}>
      {children}
      {state && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 fade-in">
          <div className="bg-surface border border-strong rounded-xl p-6 w-full max-w-sm">
            {state.title && <h3 className="font-serif italic text-2xl text-main mb-2">{state.title}</h3>}
            <p className="text-sm text-mute whitespace-pre-line leading-relaxed mb-5">{state.message}</p>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => close(false)}
                className="px-4 py-2 text-xs font-medium text-mute hover:text-main transition-colors"
              >
                {state.cancelLabel || 'キャンセル'}
              </button>
              <button
                onClick={() => close(true)}
                className={`px-4 py-2 text-xs font-semibold rounded-md transition-all ${
                  state.danger
                    ? 'bg-danger text-bg hover:opacity-90'
                    : 'bg-accent text-bg hover:opacity-90'
                }`}
              >
                {state.confirmLabel || '実行'}
              </button>
            </div>
          </div>
        </div>
      )}
    </ConfirmContext.Provider>
  );
};

const useConfirm = () => React.useContext(ConfirmContext);

// ───── Primitives ─────
const Input = React.forwardRef(({ className = '', ...props }, ref) => (
  <input
    ref={ref}
    className={`bg-main border border-line rounded-md px-3 py-2 text-sm text-main placeholder:text-dim focus:outline-none focus:border-accent transition-colors ${className}`}
    {...props}
  />
));

const Select = React.forwardRef(({ className = '', children, ...props }, ref) => (
  <select
    ref={ref}
    className={`bg-main border border-line rounded-md px-3 py-2 text-sm text-main focus:outline-none focus:border-accent transition-colors appearance-none ${className}`}
    style={{
      backgroundImage: `url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8' fill='none'%3e%3cpath d='M1 1L6 6L11 1' stroke='%238F867A' stroke-width='1.5' stroke-linecap='round'/%3e%3c/svg%3e")`,
      backgroundRepeat: 'no-repeat',
      backgroundPosition: 'right 0.75rem center',
      paddingRight: '2rem',
    }}
    {...props}
  >
    {children}
  </select>
));

const Button = ({ variant = 'ghost', size = 'md', className = '', children, ...props }) => {
  const sizes = {
    sm: 'px-2.5 py-1.5 text-xs',
    md: 'px-3.5 py-2 text-xs',
    lg: 'px-5 py-3 text-sm',
  };
  const variants = {
    primary: 'bg-accent text-bg hover:opacity-90 font-semibold',
    ghost: 'border border-line text-mute hover:text-main hover:border-strong',
    danger: 'border border-line text-mute hover:text-danger hover:bg-danger-dim',
    solid: 'bg-surface-2 border border-line text-main hover:border-strong',
    accent: 'border border-accent text-accent hover:bg-accent-dim font-semibold',
  };
  return (
    <button
      className={`rounded-md transition-all flex items-center gap-2 whitespace-nowrap ${sizes[size]} ${variants[variant]} disabled:opacity-30 disabled:cursor-not-allowed ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};

const Card = ({ title, eyebrow, action, children, className = '' }) => (
  <section className={`bg-surface border border-line rounded-xl ${className}`}>
    {(title || eyebrow || action) && (
      <header className="flex items-start justify-between px-5 py-4 border-b border-line">
        <div>
          {eyebrow && <div className="text-[10px] text-dim uppercase tracking-[0.2em] font-medium mb-1">{eyebrow}</div>}
          {title && <h2 className="font-serif italic text-xl text-main leading-none">{title}</h2>}
        </div>
        {action}
      </header>
    )}
    <div className="p-5">{children}</div>
  </section>
);

// ───── Main Component ─────
const ShiftSchedulerInner = () => {
  const toast = useToast();
  const confirm = useConfirm();

  const savedData = useMemo(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) return JSON.parse(saved);
    } catch (e) {
      console.error('データの読み込みに失敗しました', e);
    }
    return null;
  }, []);

  const [stores, setStores] = useState(savedData?.stores || ['A店', 'B店', 'C店']);
  const [staffList, setStaffList] = useState(savedData?.staffList || ['山田', '鈴木', '加藤']);
  const [newStaffName, setNewStaffName] = useState('');
  const [newStoreName, setNewStoreName] = useState('');

  const [storePriorities, setStorePriorities] = useState(savedData?.storePriorities || {
    'A店': ['山田', '鈴木', '加藤'],
    'B店': ['山田', '鈴木', '加藤'],
    'C店': ['山田', '鈴木', '加藤'],
  });

  const [ngCombinations, setNgCombinations] = useState(savedData?.ngCombinations || []);
  const [requests, setRequests] = useState(savedData?.requests || {});
  const [schedule, setSchedule] = useState(savedData?.schedule || {});
  const [isLocked, setIsLocked] = useState(savedData?.isLocked || false);
  const [activeTab, setActiveTab] = useState('master');

  const [showEmailImport, setShowEmailImport] = useState(false);
  const [emailText, setEmailText] = useState('');

  const [viewMode, setViewMode] = useState('admin');
  const [selectedStaff, setSelectedStaff] = useState('');

  // FIX: ng selects via state instead of getElementById
  const [ngStaff1, setNgStaff1] = useState('');
  const [ngStaff2, setNgStaff2] = useState('');

  // FIX: toggleLock now actually flips state
  const toggleLock = useCallback(() => {
    setIsLocked(prev => {
      const next = !prev;
      setTimeout(() => {
        toast(next ? '申請を締め切りました\nスタッフは希望を変更できません' : '申請を再開しました', 'success');
      }, 100);
      return next;
    });
  }, [toast]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const staffParam = params.get('staff');
    if (staffParam && staffList.includes(staffParam)) {
      setViewMode('staff');
      setSelectedStaff(staffParam);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const dataToSave = { stores, staffList, storePriorities, ngCombinations, requests, schedule, isLocked };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(dataToSave));
  }, [stores, staffList, storePriorities, ngCombinations, requests, schedule, isLocked]);

  const resetAllData = async () => {
    const ok = await confirm({
      title: 'すべて削除します',
      message: 'この操作は取り消せません。\nスタッフ・店舗・希望・シフト表が全て消去されます。',
      confirmLabel: '削除する', cancelLabel: 'やめる', danger: true,
    });
    if (!ok) return;
    localStorage.removeItem(STORAGE_KEY);
    window.location.reload();
  };

  const downloadJSON = () => {
    const data = { version: VERSION, stores, staffList, storePriorities, ngCombinations, requests, schedule, isLocked, savedAt: new Date().toISOString() };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `シフトデータ_${VERSION}_${new Date().toLocaleDateString('ja-JP')}.json`;
    link.click();
    toast('バックアップを保存しました', 'success');
  };

  const loadJSON = (event) => {
    const file = event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target.result);
        if (data.stores) setStores(data.stores);
        if (data.staffList) setStaffList(data.staffList);
        if (data.storePriorities) setStorePriorities(data.storePriorities);
        if (data.ngCombinations) setNgCombinations(data.ngCombinations);
        if (data.requests) setRequests(data.requests);
        if (data.schedule) setSchedule(data.schedule);
        if (data.isLocked !== undefined) setIsLocked(data.isLocked);
        toast('データを読み込みました', 'success');
      } catch (error) {
        console.error('JSON読み込みエラー:', error);
        toast('ファイルの読み込みに失敗しました', 'error');
      }
    };
    reader.readAsText(file);
    event.target.value = '';
  };

  const parseEmailText = (text) => {
    const lines = text.split('\n').map(l => l.trim()).filter(l => l);
    let staffName = '';
    const newRequests = {};
    let importedCount = 0;

    for (let line of lines) {
      if (line.startsWith('名前:') || line.startsWith('名前：')) {
        staffName = line.replace(/名前[::：]\s*/, '').trim();
        if (!staffList.includes(staffName)) {
          toast(`${staffName}はスタッフマスタに未登録です`, 'error');
          return;
        }
        continue;
      }
      const dayMatch = line.match(/^(月曜日|火曜日|水曜日|木曜日|金曜日|土曜日|日曜日)[::：]\s*(.*)$/);
      if (dayMatch && staffName) {
        const day = dayMatch[1];
        const storesText = dayMatch[2].trim();
        if (storesText && storesText !== '休み' && storesText !== '休') {
          const requestedStores = storesText.split(/[,、，]/).map(s => s.trim()).filter(s => s);
          requestedStores.forEach(storeName => {
            if (stores.includes(storeName)) {
              const key = `${staffName}-${day}-${storeName}`;
              newRequests[key] = { staffName, day, store: storeName };
              importedCount++;
            }
          });
        }
      }
    }

    if (importedCount > 0) {
      setRequests(prev => ({ ...prev, ...newRequests }));
      toast(`${staffName}さんの希望を${importedCount}件反映しました`, 'success');
      setActiveTab('request');
    } else {
      toast('希望データが見つかりませんでした\n形式を確認してください', 'error');
    }
  };

  const addStaff = () => {
    const name = newStaffName.trim();
    if (!name) return;
    if (staffList.includes(name)) { toast('同じ名前のスタッフが存在します', 'error'); return; }
    setStaffList([...staffList, name]);
    setStorePriorities(prev => {
      const updated = { ...prev };
      stores.forEach(store => { updated[store] = [...(updated[store] || []), name]; });
      return updated;
    });
    setNewStaffName('');
  };

  const removeStaff = async (staffName) => {
    const ok = await confirm({
      title: `${staffName}を削除`,
      message: `${staffName}さんの希望・NG組み合わせ・優先順位も同時に削除されます。`,
      confirmLabel: '削除', danger: true,
    });
    if (!ok) return;
    setStaffList(staffList.filter(s => s !== staffName));
    setStorePriorities(prev => {
      const updated = { ...prev };
      stores.forEach(store => { updated[store] = (updated[store] || []).filter(s => s !== staffName); });
      return updated;
    });
    setRequests(prev => {
      const updated = { ...prev };
      Object.keys(updated).forEach(key => { if (key.startsWith(`${staffName}-`)) delete updated[key]; });
      return updated;
    });
    setNgCombinations(prev => prev.filter(ng => ng.staff1 !== staffName && ng.staff2 !== staffName));
  };

  const addStore = () => {
    const name = newStoreName.trim();
    if (!name) return;
    if (stores.includes(name)) { toast('同じ名前の店舗が存在します', 'error'); return; }
    setStores([...stores, name]);
    setStorePriorities(prev => ({ ...prev, [name]: [...staffList] }));
    setNewStoreName('');
  };

  const removeStore = async (storeName) => {
    if (stores.length <= 1) { toast('店舗は最低1つ必要です', 'error'); return; }
    const ok = await confirm({ title: `${storeName}を削除`, message: `この店舗と関連する希望が削除されます。`, confirmLabel: '削除', danger: true });
    if (!ok) return;
    setStores(stores.filter(s => s !== storeName));
    setStorePriorities(prev => { const u = { ...prev }; delete u[storeName]; return u; });
    setRequests(prev => {
      const u = { ...prev };
      Object.keys(u).forEach(key => { if (key.includes(`-${storeName}`)) delete u[key]; });
      return u;
    });
  };

  const addNgCombination = () => {
    if (!ngStaff1 || !ngStaff2 || ngStaff1 === ngStaff2) return;
    const exists = ngCombinations.some(
      ng => (ng.staff1 === ngStaff1 && ng.staff2 === ngStaff2) ||
            (ng.staff1 === ngStaff2 && ng.staff2 === ngStaff1)
    );
    if (exists) { toast('既に登録されています', 'error'); return; }
    setNgCombinations([...ngCombinations, { staff1: ngStaff1, staff2: ngStaff2 }]);
    setNgStaff1(''); setNgStaff2('');
  };

  const moveStaffUp = (store, staffName) => {
    setStorePriorities(prev => {
      const list = [...(prev[store] || [])];
      const i = list.indexOf(staffName);
      if (i > 0) [list[i - 1], list[i]] = [list[i], list[i - 1]];
      return { ...prev, [store]: list };
    });
  };

  const moveStaffDown = (store, staffName) => {
    setStorePriorities(prev => {
      const list = [...(prev[store] || [])];
      const i = list.indexOf(staffName);
      if (i < list.length - 1 && i !== -1) [list[i], list[i + 1]] = [list[i + 1], list[i]];
      return { ...prev, [store]: list };
    });
  };

  const toggleRequest = (staffName, day, store) => {
    if (isLocked && viewMode === 'staff') {
      toast('申請期間は締め切られました', 'error');
      return;
    }
    const key = `${staffName}-${day}-${store}`;
    setRequests(prev => {
      const n = { ...prev };
      if (n[key]) delete n[key]; else n[key] = { staffName, day, store };
      return n;
    });
  };

  const isNgCombination = (a, b) =>
    ngCombinations.some(ng => (ng.staff1 === a && ng.staff2 === b) || (ng.staff1 === b && ng.staff2 === a));

  const generateSchedule = async () => {
    if (Object.keys(requests).length === 0) {
      const ok = await confirm({
        title: '希望が未入力です',
        message: 'シフト希望が1件も入力されていません。\n空のシフト表を生成しますか?',
        confirmLabel: '生成する',
      });
      if (!ok) return;
    }
    const newSchedule = {};
    const assignedPerDay = {};
    let total = 0;
    let ngSkipped = 0;

    DAYS.forEach(day => {
      assignedPerDay[day] = new Set();
      stores.forEach(store => {
        const key = `${day}-${store}`;
        newSchedule[key] = [];
        const priority = storePriorities[store] || [];
        for (const staffName of priority) {
          if (newSchedule[key].length >= 2) break;
          const reqKey = `${staffName}-${day}-${store}`;
          if (requests[reqKey] && !assignedPerDay[day].has(staffName)) {
            const ngHit = newSchedule[key].some(s => isNgCombination(staffName, s));
            if (ngHit) { ngSkipped++; continue; }
            newSchedule[key].push(staffName);
            assignedPerDay[day].add(staffName);
            total++;
          }
        }
      });
    });

    setSchedule(newSchedule);
    setActiveTab('schedule');
    const detail = ngSkipped > 0 ? `\nNG組み合わせで${ngSkipped}件スキップ` : '';
    toast(`シフト生成完了\n配置${total}件${detail}`, 'success');
  };

  const downloadCSV = () => {
    if (Object.keys(schedule).length === 0) {
      toast('先にシフトを自動生成してください', 'error');
      return;
    }
    let csv = '曜日,' + stores.join(',') + '\n';
    DAYS.forEach(day => {
      let row = day;
      stores.forEach(store => {
        const s = schedule[`${day}-${store}`] || [];
        row += ',' + (s.length > 0 ? s.join('・') : '');
      });
      csv += row + '\n';
    });
    const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `シフト表_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 100);
    toast('CSVを保存しました', 'success');
  };

  const staffScheduleFor = (staffName) =>
    DAYS.map(day => ({
      day,
      stores: stores.filter(s => (schedule[`${day}-${s}`] || []).includes(staffName)),
    }));

  const emailBodyFor = (staffName) => {
    const sched = staffScheduleFor(staffName);
    const workDays = sched.filter(s => s.stores.length > 0).length;
    let text = `${staffName}さんの今週のシフト\n━━━━━━━━━━━━━━━━\n\n`;
    sched.forEach(({ day, stores: ss }) => {
      text += `${day}: ${ss.length > 0 ? ss.join('、') : '休み'}\n`;
    });
    text += `\n━━━━━━━━━━━━━━━━\n勤務日数: ${workDays}日\n`;
    text += `\n※ ${new Date().toLocaleDateString('ja-JP')}生成\n※ 変更は管理者まで`;
    return text;
  };

  const copyStaffShift = async (staffName) => {
    try {
      await navigator.clipboard.writeText(emailBodyFor(staffName));
      toast(`${staffName}さんのシフトをコピーしました`, 'success');
    } catch {
      toast('コピーに失敗しました', 'error');
    }
  };

  const mailtoStaffShift = (staffName) => {
    const subject = `【シフト】${staffName}さんの今週のシフト`;
    const body = emailBodyFor(staffName);
    window.location.href = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  };

  const totalAssignments = useMemo(() =>
    Object.values(schedule).reduce((sum, arr) => sum + (arr?.length || 0), 0), [schedule]);
  const filledSlots = useMemo(() =>
    Object.values(schedule).filter(arr => arr && arr.length > 0).length, [schedule]);
  const totalSlots = stores.length * DAYS.length;
  const fillRate = totalSlots > 0 ? Math.round((filledSlots / totalSlots) * 100) : 0;

  const TABS = [
    { id: 'master', icon: UserPlus, label: 'マスタ' },
    { id: 'settings', icon: Settings, label: '優先順位' },
    { id: 'request', icon: Users, label: '希望入力' },
    { id: 'schedule', icon: Store, label: 'シフト表' },
  ];

  return (
    <div className="min-h-screen bg-main relative">
      <div className="fixed inset-0 grid-lines opacity-[0.15] pointer-events-none" />

      <div className="relative max-w-7xl mx-auto px-6 py-6">
        {/* ─── Header ─── */}
        <header className="flex items-start justify-between mb-8 pb-6 border-b border-line">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-8 h-8 border border-accent text-accent rounded-md flex items-center justify-center">
                <Calendar size={15} />
              </div>
              <span className="text-[10px] text-dim uppercase tracking-[0.25em] font-medium">Shift Command {VERSION}</span>
              {viewMode === 'staff' && (
                <span className="text-[10px] text-accent uppercase tracking-[0.2em] font-semibold border border-accent px-2 py-0.5 rounded">
                  Staff Mode
                </span>
              )}
            </div>
            <h1 className="font-serif italic text-5xl text-main leading-none tracking-tight">
              シフト自動作成<span className="text-accent">.</span>
            </h1>
            <p className="text-sm text-mute mt-3 max-w-lg">
              {viewMode === 'admin'
                ? 'スタッフ・店舗を管理し、条件に合わせてシフトを自動生成します。'
                : 'あなたのシフト希望を入力してください。'}
            </p>
          </div>

          <div className="flex items-center gap-2 flex-wrap justify-end">
            <div className="flex items-center gap-2 mr-2 text-[11px] text-mute">
              <span className={`w-1.5 h-1.5 rounded-full ${isLocked ? 'bg-danger pulse-dot' : 'bg-success'}`} />
              <span className="font-mono uppercase tracking-wider">{isLocked ? 'Locked' : 'Open'}</span>
            </div>

            <Button
              variant={viewMode === 'staff' ? 'accent' : 'ghost'}
              onClick={() => {
                if (viewMode === 'admin') { setViewMode('staff'); setSelectedStaff(''); }
                else { setViewMode('admin'); setActiveTab('master'); }
              }}
            >
              {viewMode === 'admin' ? <><Users size={13} />スタッフ</> : <><Settings size={13} />管理者</>}
            </Button>

            {viewMode === 'admin' && (
              <>
                <Button variant={isLocked ? 'accent' : 'ghost'} onClick={toggleLock}>
                  {isLocked ? <><Unlock size={13} />再開</> : <><Lock size={13} />締切</>}
                </Button>
                <Button variant="ghost" onClick={downloadJSON} title="バックアップ">
                  <Download size={13} />保存
                </Button>
                <label className="cursor-pointer">
                  <input type="file" accept=".json" onChange={loadJSON} className="hidden" />
                  <span className="rounded-md transition-all flex items-center gap-2 whitespace-nowrap px-3.5 py-2 text-xs border border-line text-mute hover:text-main hover:border-strong">
                    <Upload size={13} />読込
                  </span>
                </label>
                <Button variant="danger" onClick={resetAllData} title="全リセット">
                  <RotateCcw size={13} />
                </Button>
              </>
            )}
          </div>
        </header>

        {/* ─── Nav Tabs ─── */}
        {viewMode === 'admin' ? (
          <nav className="flex gap-1 mb-8 border-b border-line">
            {TABS.map(({ id, icon: Icon, label }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex items-center gap-2 px-4 py-3 text-xs font-medium border-b-2 -mb-px transition-colors ${
                  activeTab === id ? 'border-accent text-accent' : 'border-transparent text-mute hover:text-main'
                }`}
              >
                <Icon size={13} />{label}
              </button>
            ))}
          </nav>
        ) : (
          <div className="mb-8">
            <Card title="スタッフ選択" eyebrow="Staff Picker">
              <Select value={selectedStaff} onChange={e => setSelectedStaff(e.target.value)} className="w-full">
                <option value="">選択してください...</option>
                {staffList.map(s => <option key={s} value={s}>{s}</option>)}
              </Select>
            </Card>
          </div>
        )}

        {/* ═══════════ MASTER TAB ═══════════ */}
        {viewMode === 'admin' && activeTab === 'master' && (
          <div className="space-y-5 fade-in">
            <Card title="スタッフ" eyebrow="Staff · 01" action={<span className="text-xs text-dim font-mono">{staffList.length} PERSONS</span>}>
              <div className="flex gap-2 mb-4">
                <Input
                  value={newStaffName}
                  onChange={e => setNewStaffName(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && addStaff()}
                  placeholder="スタッフ名を入力"
                  className="flex-1"
                />
                <Button variant="primary" onClick={addStaff}><UserPlus size={13} />追加</Button>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {staffList.map(s => (
                  <div key={s} className="bg-surface-2 border border-line rounded-md px-3 py-2.5 flex items-center justify-between group hover:border-strong transition-colors">
                    <span className="text-sm text-main">{s}</span>
                    <button onClick={() => removeStaff(s)} className="text-dim hover:text-danger opacity-0 group-hover:opacity-100 transition-all">
                      <Trash2 size={13} />
                    </button>
                  </div>
                ))}
                {staffList.length === 0 && <div className="col-span-full text-center py-6 text-dim text-sm">未登録</div>}
              </div>
            </Card>

            <Card title="店舗" eyebrow="Stores · 02" action={<span className="text-xs text-dim font-mono">{stores.length} LOCATIONS</span>}>
              <div className="flex gap-2 mb-4">
                <Input
                  value={newStoreName}
                  onChange={e => setNewStoreName(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && addStore()}
                  placeholder="店舗名を入力"
                  className="flex-1"
                />
                <Button variant="primary" onClick={addStore}><Store size={13} />追加</Button>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {stores.map(s => (
                  <div key={s} className="bg-surface-2 border border-line rounded-md px-3 py-2.5 flex items-center justify-between group hover:border-strong transition-colors">
                    <span className="text-sm text-main">{s}</span>
                    <button onClick={() => removeStore(s)} className="text-dim hover:text-danger opacity-0 group-hover:opacity-100 transition-all">
                      <Trash2 size={13} />
                    </button>
                  </div>
                ))}
              </div>
            </Card>

            <Card title="NG組み合わせ" eyebrow="Restrictions · 03" action={<span className="text-xs text-dim font-mono">{ngCombinations.length} RULES</span>}>
              <p className="text-xs text-mute mb-4">同じ店舗に入れないスタッフの組み合わせを登録します</p>
              <div className="flex gap-2 mb-4">
                <Select value={ngStaff1} onChange={e => setNgStaff1(e.target.value)} className="flex-1">
                  <option value="">スタッフA</option>
                  {staffList.map(s => <option key={s} value={s}>{s}</option>)}
                </Select>
                <span className="flex items-center text-dim font-mono">×</span>
                <Select value={ngStaff2} onChange={e => setNgStaff2(e.target.value)} className="flex-1">
                  <option value="">スタッフB</option>
                  {staffList.filter(s => s !== ngStaff1).map(s => <option key={s} value={s}>{s}</option>)}
                </Select>
                <Button variant="primary" onClick={addNgCombination} disabled={!ngStaff1 || !ngStaff2}>追加</Button>
              </div>
              <div className="space-y-1.5">
                {ngCombinations.map((ng, i) => (
                  <div key={i} className="bg-danger-dim border border-line rounded-md px-4 py-2.5 flex items-center justify-between">
                    <span className="text-sm text-main font-mono">
                      {ng.staff1} <span className="text-danger mx-2">×</span> {ng.staff2}
                    </span>
                    <button onClick={() => setNgCombinations(ngCombinations.filter((_, x) => x !== i))} className="text-dim hover:text-danger">
                      <X size={15} />
                    </button>
                  </div>
                ))}
                {ngCombinations.length === 0 && <div className="text-center py-6 text-dim text-sm">NGルールなし</div>}
              </div>
            </Card>
          </div>
        )}

        {/* ═══════════ SETTINGS TAB ═══════════ */}
        {viewMode === 'admin' && activeTab === 'settings' && (
          <div className="fade-in">
            <Card title="店舗別 優先順位" eyebrow="Priority Matrix">
              <p className="text-xs text-mute mb-6">希望が重複した場合、上位のスタッフから優先して配置されます</p>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {stores.map(store => (
                  <div key={store} className="bg-surface-2 border border-line rounded-lg overflow-hidden">
                    <div className="px-4 py-3 border-b border-line flex items-center justify-between">
                      <span className="font-serif italic text-lg text-main">{store}</span>
                      <span className="text-[10px] text-dim font-mono uppercase tracking-wider">
                        {storePriorities[store]?.length || 0} ranked
                      </span>
                    </div>
                    <div className="p-2 space-y-1">
                      {storePriorities[store]?.map((name, i) => (
                        <div key={name} className="flex items-center justify-between px-3 py-2 rounded hover:bg-main transition-colors group">
                          <div className="flex items-center gap-3">
                            <span className="text-[10px] text-dim font-mono w-5">#{String(i + 1).padStart(2, '0')}</span>
                            <span className="text-sm text-main">{name}</span>
                          </div>
                          <div className="flex gap-0.5 opacity-30 group-hover:opacity-100 transition-opacity">
                            <button
                              onClick={() => moveStaffUp(store, name)}
                              disabled={i === 0}
                              className="p-1 text-mute hover:text-accent disabled:opacity-20 disabled:cursor-not-allowed"
                            >
                              <ChevronUp size={14} />
                            </button>
                            <button
                              onClick={() => moveStaffDown(store, name)}
                              disabled={i === storePriorities[store].length - 1}
                              className="p-1 text-mute hover:text-accent disabled:opacity-20 disabled:cursor-not-allowed"
                            >
                              <ChevronDown size={14} />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        )}

        {/* ═══════════ REQUEST TAB (admin) ═══════════ */}
        {viewMode === 'admin' && activeTab === 'request' && (
          <div className="space-y-5 fade-in">
            <Card
              title="希望入力"
              eyebrow="Requests"
              action={
                <Button variant="accent" onClick={() => setShowEmailImport(!showEmailImport)}>
                  <Mail size={13} />メールから取込
                </Button>
              }
            >
              {showEmailImport && (
                <div className="mb-5 border border-accent rounded-lg p-5 bg-accent-dim">
                  <div className="flex items-center gap-2 mb-3">
                    <FileText size={14} className="text-accent" />
                    <h3 className="font-serif italic text-lg text-main">メールから取込</h3>
                  </div>
                  <div className="bg-main rounded-md p-3 mb-3 border border-line">
                    <div className="text-[10px] text-dim uppercase tracking-widest mb-2">Example Format</div>
                    <pre className="text-xs font-mono text-mute overflow-x-auto leading-relaxed">{`名前: 山田

月曜日: A店, B店
火曜日:
水曜日: A店
木曜日: C店
金曜日:
土曜日: A店, B店
日曜日: 休み`}</pre>
                  </div>
                  <textarea
                    value={emailText}
                    onChange={e => setEmailText(e.target.value)}
                    placeholder="メール本文をペースト..."
                    className="w-full h-48 bg-main border border-line rounded-md px-3 py-2 text-sm font-mono text-main placeholder:text-dim focus:outline-none focus:border-accent transition-colors mb-3"
                  />
                  <div className="flex gap-2">
                    <Button variant="primary" onClick={() => { parseEmailText(emailText); setEmailText(''); setShowEmailImport(false); }} className="flex-1 justify-center">
                      取り込む
                    </Button>
                    <Button variant="ghost" onClick={() => { setEmailText(''); setShowEmailImport(false); }}>
                      キャンセル
                    </Button>
                  </div>
                </div>
              )}

              <p className="text-xs text-mute mb-5">セルをクリックで希望ON/OFF ・ アンバー色が希望あり</p>

              <div className="space-y-5">
                {staffList.map(staffName => {
                  const count = Object.keys(requests).filter(k => k.startsWith(`${staffName}-`)).length;
                  return (
                    <div key={staffName}>
                      <div className="flex items-center justify-between mb-2 px-1">
                        <span className="text-sm text-main font-medium">{staffName}</span>
                        <span className="text-[10px] text-dim font-mono uppercase tracking-wider">
                          {count} requests
                        </span>
                      </div>
                      <div className="overflow-x-auto border border-line rounded-md">
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="bg-surface-2">
                              <th className="text-left px-3 py-2 text-dim font-medium uppercase tracking-wider w-20">曜日</th>
                              {stores.map(s => (
                                <th key={s} className="text-center px-3 py-2 text-dim font-medium border-l border-line">{s}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {DAYS.map((day, di) => (
                              <tr key={day} className="border-t border-line">
                                <td className="px-3 py-1.5 text-mute font-mono">
                                  {DAY_SHORT[di]}<span className="text-dim">曜</span>
                                </td>
                                {stores.map(store => {
                                  const key = `${staffName}-${day}-${store}`;
                                  const on = !!requests[key];
                                  return (
                                    <td key={store} className="p-1 border-l border-line">
                                      <button
                                        onClick={() => toggleRequest(staffName, day, store)}
                                        className={`w-full py-1.5 rounded text-xs transition-all ${
                                          on
                                            ? 'bg-accent text-bg font-semibold'
                                            : 'text-dim hover:bg-surface-2 hover:text-mute'
                                        }`}
                                      >
                                        {on ? '希望' : '—'}
                                      </button>
                                    </td>
                                  );
                                })}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="mt-6 pt-6 border-t border-line flex items-center justify-between">
                <span className="text-xs text-mute font-mono">
                  TOTAL <span className="text-accent">{Object.keys(requests).length}</span> requests
                </span>
                <Button variant="primary" size="lg" onClick={generateSchedule}>
                  <Play size={15} />シフトを自動生成
                </Button>
              </div>
            </Card>
          </div>
        )}

        {/* ═══════════ SCHEDULE TAB ═══════════ */}
        {viewMode === 'admin' && activeTab === 'schedule' && (
          <div className="space-y-5 fade-in">
            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { label: 'Assignments', value: totalAssignments, suffix: '件', accent: true },
                { label: 'Open Slots', value: totalSlots - filledSlots, suffix: '件' },
                { label: 'Avg Days', value: staffList.length > 0 ? (totalAssignments / staffList.length).toFixed(1) : 0, suffix: '日' },
                { label: 'Fill Rate', value: fillRate, suffix: '%' },
              ].map(({ label, value, suffix, accent }) => (
                <div key={label} className="bg-surface border border-line rounded-lg p-4">
                  <div className="text-[10px] text-dim uppercase tracking-[0.2em] mb-2">{label}</div>
                  <div className="flex items-baseline gap-1">
                    <span className={`font-serif italic text-4xl leading-none ${accent ? 'text-accent' : 'text-main'}`}>{value}</span>
                    <span className="text-xs text-mute font-mono">{suffix}</span>
                  </div>
                </div>
              ))}
            </div>

            <Card
              title="生成シフト表"
              eyebrow="Schedule Output"
              action={<Button variant="accent" onClick={downloadCSV}><Download size={13} />CSV</Button>}
            >
              <div className="overflow-x-auto border border-line rounded-md">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-surface-2">
                      <th className="text-left px-4 py-3 text-dim text-[10px] uppercase tracking-[0.2em] font-medium w-24">Day</th>
                      {stores.map(s => (
                        <th key={s} className="text-left px-4 py-3 text-dim text-[10px] uppercase tracking-[0.2em] font-medium border-l border-line">{s}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {DAYS.map((day, di) => (
                      <tr key={day} className="border-t border-line">
                        <td className="px-4 py-3 text-mute font-mono">
                          <span className="text-main">{DAY_SHORT[di]}</span><span className="text-dim">曜日</span>
                        </td>
                        {stores.map(store => {
                          const assigned = schedule[`${day}-${store}`] || [];
                          return (
                            <td key={store} className="px-4 py-3 border-l border-line">
                              {assigned.length > 0 ? (
                                <span className="text-main">{assigned.join(' · ')}</span>
                              ) : (
                                <span className="text-dim text-xs">—</span>
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>

            {totalAssignments > 0 && (
              <Card title="スタッフ別シフト送信" eyebrow="Dispatch">
                <p className="text-xs text-mute mb-5">各スタッフ個別のシフトを抽出して共有できます</p>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {staffList.map(staff => {
                    const ss = staffScheduleFor(staff);
                    const workDays = ss.filter(x => x.stores.length > 0).length;
                    return (
                      <div key={staff} className="bg-surface-2 border border-line rounded-lg p-4 flex flex-col">
                        <div className="flex items-center justify-between mb-3">
                          <span className="font-serif italic text-lg text-main">{staff}</span>
                          <span className="text-[10px] font-mono text-accent uppercase tracking-wider">
                            {workDays} days
                          </span>
                        </div>
                        <div className="space-y-0.5 text-xs mb-4 flex-1">
                          {ss.map(({ day, stores: ssArr }, i) => (
                            <div key={day} className="flex justify-between py-0.5">
                              <span className="text-dim font-mono">{DAY_SHORT[i]}</span>
                              <span className={ssArr.length > 0 ? 'text-main' : 'text-dim'}>
                                {ssArr.length > 0 ? ssArr.join('・') : '休'}
                              </span>
                            </div>
                          ))}
                        </div>
                        <div className="flex gap-1.5 pt-3 border-t border-line">
                          <Button variant="ghost" size="sm" onClick={() => mailtoStaffShift(staff)} className="flex-1 justify-center">
                            <Mail size={12} />メール
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => copyStaffShift(staff)} className="flex-1 justify-center">
                            <Copy size={12} />コピー
                          </Button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </Card>
            )}

            <div className="bg-surface border border-line rounded-lg p-5">
              <div className="text-[10px] text-dim uppercase tracking-[0.2em] mb-3 font-medium">Rules</div>
              <ul className="text-xs text-mute space-y-1.5">
                <li>・ 各店舗には最大2人まで配置されます</li>
                <li>・ スタッフは1日に複数店舗に入れません</li>
                <li>・ 希望重複時は店舗別の優先順位で決定します</li>
                <li>・ NG組み合わせのペアは同じ店舗に入りません</li>
                <li>・ 誰も希望していない枠は未配置になります</li>
              </ul>
            </div>
          </div>
        )}

        {/* ═══════════ STAFF MODE ═══════════ */}
        {viewMode === 'staff' && selectedStaff && (
          <div className="space-y-5 fade-in">
            <Card title={`${selectedStaff}さんのシフト希望`} eyebrow="Personal Input">
              <div className={`mb-5 p-3 rounded-md border ${isLocked ? 'border-danger bg-danger-dim' : 'border-accent bg-accent-dim'}`}>
                <div className="flex items-center gap-2 text-sm">
                  {isLocked ? <Lock size={14} className="text-danger" /> : <Unlock size={14} className="text-accent" />}
                  <span className={isLocked ? 'text-danger' : 'text-accent'}>
                    {isLocked ? '申請期間は締め切られています' : '申請受付中'}
                  </span>
                </div>
              </div>

              <div className="overflow-x-auto border border-line rounded-md mb-5">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-surface-2">
                      <th className="text-left px-4 py-3 text-dim text-[10px] uppercase tracking-[0.2em] w-24">Day</th>
                      {stores.map(s => (
                        <th key={s} className="text-center px-4 py-3 text-dim text-[10px] uppercase tracking-[0.2em] border-l border-line">{s}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {DAYS.map((day, di) => (
                      <tr key={day} className="border-t border-line">
                        <td className="px-4 py-2 text-mute font-mono">
                          <span className="text-main">{DAY_SHORT[di]}</span><span className="text-dim">曜日</span>
                        </td>
                        {stores.map(store => {
                          const key = `${selectedStaff}-${day}-${store}`;
                          const on = !!requests[key];
                          return (
                            <td key={store} className="p-1.5 border-l border-line">
                              <button
                                onClick={() => toggleRequest(selectedStaff, day, store)}
                                disabled={isLocked}
                                className={`w-full py-3 rounded text-sm font-medium transition-all ${
                                  on
                                    ? 'bg-accent text-bg'
                                    : 'text-dim hover:bg-surface-2 hover:text-mute'
                                } ${isLocked ? 'opacity-50 cursor-not-allowed' : ''}`}
                              >
                                {on ? <Check size={14} className="inline" /> : '休'}
                              </button>
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="flex gap-2 mb-5">
                <Button variant="primary" size="lg" className="flex-1 justify-center" disabled={isLocked} onClick={() => toast('希望を保存しました', 'success')}>
                  <Check size={15} />保存
                </Button>
                {!isLocked && (
                  <Button
                    variant="danger"
                    size="lg"
                    onClick={async () => {
                      const ok = await confirm({ message: `${selectedStaff}さんの全希望をクリアしますか?`, confirmLabel: 'クリア', danger: true });
                      if (!ok) return;
                      setRequests(prev => {
                        const u = { ...prev };
                        Object.keys(u).forEach(k => { if (k.startsWith(`${selectedStaff}-`)) delete u[k]; });
                        return u;
                      });
                      toast('希望をクリアしました', 'success');
                    }}
                  >
                    クリア
                  </Button>
                )}
              </div>

              <div className="bg-surface-2 border border-line rounded-md p-4">
                <div className="flex items-center gap-2 mb-2">
                  <LinkIcon size={13} className="text-dim" />
                  <span className="text-[10px] text-dim uppercase tracking-widest font-medium">Personal URL</span>
                </div>
                <div className="flex gap-2">
                  <Input
                    value={`${window.location.origin}${window.location.pathname}?staff=${encodeURIComponent(selectedStaff)}`}
                    readOnly
                    className="flex-1 font-mono text-xs"
                    onClick={e => e.target.select()}
                  />
                  <Button
                    variant="ghost"
                    onClick={() => {
                      const url = `${window.location.origin}${window.location.pathname}?staff=${encodeURIComponent(selectedStaff)}`;
                      navigator.clipboard.writeText(url).then(() => toast('URLをコピーしました', 'success'));
                    }}
                  >
                    <Copy size={13} />
                  </Button>
                </div>
                <p className="text-[11px] text-dim mt-2">ブックマークしておくと次回から直接アクセスできます</p>
              </div>
            </Card>
          </div>
        )}

        <footer className="mt-12 pt-6 border-t border-line flex items-center justify-between text-[10px] text-dim uppercase tracking-widest font-mono">
          <span>Auto-saved to browser</span>
          <span>{VERSION} · Shift Command</span>
        </footer>
      </div>
    </div>
  );
};

const ShiftScheduler = () => (
  <ToastProvider>
    <ConfirmProvider>
      <ShiftSchedulerInner />
    </ConfirmProvider>
  </ToastProvider>
);

export default ShiftScheduler;
