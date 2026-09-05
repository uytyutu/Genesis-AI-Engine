import { OfficeOrderResultPage } from "../../../components/office/OfficeOrderResultPage";

export default async function OfficeOrderRoute({
  params,
}: {
  params: Promise<{ jobId: string }>;
}) {
  const { jobId } = await params;
  return <OfficeOrderResultPage jobId={jobId} />;
}
