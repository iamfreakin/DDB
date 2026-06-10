import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="site-header">
      <div className="shell header-inner">
        <Link href="/" className="wordmark">
          BRAND STUDIO
        </Link>
        <nav className="header-nav" aria-label="주요 메뉴">
          <Link href="/#process">서비스</Link>
          <Link href="/#recent">최근 작업</Link>
          <Link href="/studio/new" className="button small primary">
            새 브랜드 시작
          </Link>
        </nav>
      </div>
    </header>
  );
}
