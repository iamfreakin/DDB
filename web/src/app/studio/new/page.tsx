import type { Metadata } from "next";
import { NewBrandForm } from "@/components/new-brand-form";
import { SiteHeader } from "@/components/site-header";

export const metadata: Metadata = {
  title: "새 브랜드",
};

export default function NewBrandPage() {
  return (
    <>
      <SiteHeader />
      <main className="page">
        <div className="shell">
          <div className="page-head">
            <div>
              <p className="eyebrow">New brand</p>
              <h1>브랜드의 기준부터 시작합니다.</h1>
            </div>
            <p className="page-description">
              가게의 상품, 고객, 강점을 입력하면 이후의 분석과 콘텐츠가 같은
              목소리를 유지합니다. 입력한 정보는 언제든 새 버전으로 수정할 수
              있습니다.
            </p>
          </div>
          <NewBrandForm />
        </div>
      </main>
    </>
  );
}
