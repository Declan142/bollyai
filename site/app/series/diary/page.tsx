import { VerdictDiary } from "../../../components/VerdictDiary";
import { pageSeo } from "../../../lib/seo";

// The Verdict Diary is a device-local tool (localStorage, no server content), so it is marked
// noindex - there is nothing to rank, and it keeps the apex topical map clean. The SEO lane owns
// global strategy; this single robots flag is local to the surface and does not touch globals.
export const metadata = {
  title: "Verdict Diary - track your shows privately",
  description:
    "Your private, device-local watch diary: save shows, set your own score next to BollyAI's, and keep notes. No account, nothing leaves your browser.",
  ...pageSeo({ path: "/series/diary/" }),
  robots: { index: false, follow: true }
};

export default function VerdictDiaryPage() {
  return <VerdictDiary />;
}
