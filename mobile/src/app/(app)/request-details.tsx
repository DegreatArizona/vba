import { useLocalSearchParams } from "expo-router";

import { RequestDetailScreen } from "../../../components/RequestDetailScreen";

export default function RequestDetailsRoute() {
  const { requestId } = useLocalSearchParams<{ requestId?: string | string[] }>();
  const resolvedId = Array.isArray(requestId) ? requestId[0] ?? "" : requestId ?? "";

  return <RequestDetailScreen requestId={resolvedId} />;
}
