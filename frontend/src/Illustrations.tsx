import type { CSSProperties, ReactNode } from 'react';

export function Icon({ name, size = 20 }: { name: string; size?: number }) {
  const paths: Record<string, ReactNode> = {
    chat: <><path d="M21 11.5a8.5 8.5 0 0 1-8.5 8.5H4l-2 2V11.5a9.5 9.5 0 0 1 19 0Z"/><path d="M7 10h9M7 14h6"/></>,
    sources: <><path d="M10 5H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-5"/><path d="m13 3 8 0 0 8M21 3l-11 11"/></>,
    documents: <><path d="M7 3h8l5 5v13H7z"/><path d="M15 3v6h5M4 6v15M10 13h7M10 17h5"/></>,
    search: <><circle cx="10.5" cy="10.5" r="7"/><path d="m16 16 5 5"/></>,
    arrow: <><path d="M12 20V4m-6 6 6-6 6 6"/></>,
    user: <><circle cx="12" cy="8" r="3.5"/><path d="M5 21v-2a7 7 0 0 1 14 0v2"/></>,
    sparkle: <><path d="m12 2 2.6 7.4L22 12l-7.4 2.6L12 22l-2.6-7.4L2 12l7.4-2.6Z"/><path d="m20 2 .5 1.5L22 4l-1.5.5L20 6l-.5-1.5L18 4l1.5-.5Z"/></>,
    shield: <><path d="m12 2 8 3v6c0 5-8 11-8 11S4 16 4 11V5Z"/><path d="m8 11 3 3 5-6"/></>,
    chevron: <path d="m9 5 7 7-7 7"/>,
    cap: <><path d="m2 8 10-5 10 5-10 5ZM6 10v7c4 3 8 3 12 0v-7M22 8v8"/></>,
    calendar: <><rect x="3" y="5" width="18" height="16" rx="3"/><path d="M7 2v6M17 2v6M3 11h18M7 15h2M13 15h4"/></>,
    globe: <><circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18"/></>,
    heart: <path d="M20.5 5.5a5 5 0 0 0-7 0L12 7l-1.5-1.5a5 5 0 0 0-7 7L12 21l8.5-8.5a5 5 0 0 0 0-7Z"/>,
    help: <><circle cx="12" cy="12" r="9"/><path d="M9 9a3 3 0 1 1 4 2.8c-1 .4-1 1.2-1 2.2M12 17h.01"/></>,
  };
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.65" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name] || paths.documents}</svg>;
}

export function AssistantAvatar({ small = false }: { small?: boolean }) {
  return <span className={`assistant-avatar ${small ? 'avatar-small' : ''}`} aria-hidden="true"><img src="/images/assistant-eih.png" alt=""/><span className="avatar-presence"/></span>;
}

export function AcademicIllustration({ compact = false }: { compact?: boolean }) {
  return <svg className={`academic-illustration ${compact ? 'compact' : ''}`} viewBox="0 0 260 150" fill="none" aria-hidden="true" style={{ '--art-delay': compact ? '0s' : '1s' } as CSSProperties}>
    <ellipse cx="133" cy="133" rx="104" ry="10" fill="#9C85D5" opacity=".16"/>
    <path d="M47 103h135v24H47c-13 0-13-24 0-24Z" fill="#B7A0EF"/><path d="M51 108h130v14H51c-7 0-7-14 0-14Z" fill="#F9F6FF"/>
    <path d="m65 80 127 9-2 24-128-9c-12-1-9-25 3-24Z" fill="#69C9BD"/><path d="m69 86 117 8-1 13-117-8c-7 0-6-14 1-13Z" fill="#E3F9F4"/>
    <path d="M48 65h134v24H48c-12 0-12-24 0-24Z" fill="#8165DB"/><path d="M53 71h126v12H53c-6 0-6-12 0-12Z" fill="#F6F1FF"/>
    <path d="m89 44 46-22 48 22-48 22Z" fill="#35366D"/><path d="M108 57v14c16 10 37 10 52 0V57l-25 12Z" fill="#53509B"/>
    <path d="m179 47 2 29" stroke="#D1B66C" strokeWidth="3"/><circle cx="181" cy="78" r="4" fill="#D1B66C"/>
    <path d="M205 117c-17-16-22-41-14-55 21 11 23 31 14 55Z" fill="#69C9BD"/><path d="M205 116c-2-22 10-40 24-42 6 21-6 37-24 42Z" fill="#A6DFD0"/>
    <path d="M189 115h33l-5 20h-23Z" fill="#E2D8F6"/><path d="m44 41 3-8 3 8 8 3-8 3-3 8-3-8-8-3Z" fill="#B7A0EF"/><circle cx="216" cy="35" r="4" fill="#69C9BD"/>
  </svg>;
}
