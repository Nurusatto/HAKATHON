import { BlockIpForm } from "../blacklist/BlockIpForm/BlockIpForm";
import { ExportLogsButton } from "./export";
import { List } from "./list";

export default function AnomaliesPage() {
  return (
    <section className="flex gap-3.5 flex-col">
      <BlockIpForm />
      <ExportLogsButton />
      <List />
    </section>
  );
}
