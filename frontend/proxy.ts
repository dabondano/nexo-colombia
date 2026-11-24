import { NextResponse, type NextRequest } from "next/server";
import { constitutionProvisionPath, recordExists } from "@/lib/api";
import { LESSONS } from "@/lib/lessons";

/**
 * Answers HTTP 404 for record pages whose record does not exist.
 *
 * With Cache Components the page shell is sent before the record is looked up, so a
 * `notFound()` inside the page can only show the "Página no encontrada" UI with status
 * 200. Next.js recommends doing the check here, before rendering starts. The check is a
 * HEAD request to the API that does not load the record. If the API cannot answer, the
 * request goes through and the page explains the problem.
 */
const LESSON_SLUGS = new Set(LESSONS.map((lesson) => lesson.slug));

function safeDecode(text: string): string | null {
  try {
    return decodeURIComponent(text);
  } catch {
    return null;
  }
}

const MALFORMED = Symbol("malformed");

function apiPathFor(pathname: string): string | typeof MALFORMED | null {
  const [, section, key, ...rest] = pathname.split("/");
  if (!key || rest.length > 0) return null;
  const decoded = safeDecode(key);
  if (decoded === null) return MALFORMED;
  switch (section) {
    case "instituciones":
      return `/institutions/${encodeURIComponent(decoded)}`;
    case "legislacion":
      return `/initiatives/${encodeURIComponent(decoded)}`;
    case "constitucion":
      return constitutionProvisionPath(decoded);
    default:
      return null;
  }
}

function notFoundResponse(request: NextRequest): NextResponse {
  // Rewriting to a path with no route renders app/not-found.tsx with status 404.
  return NextResponse.rewrite(new URL("/_registro-no-encontrado", request.url));
}

export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (pathname.startsWith("/aprender/")) {
    const slug = safeDecode(pathname.slice("/aprender/".length));
    return slug !== null && LESSON_SLUGS.has(slug) ? NextResponse.next() : notFoundResponse(request);
  }

  const apiPath = apiPathFor(pathname);
  if (apiPath === MALFORMED) return notFoundResponse(request);
  if (apiPath && !(await recordExists(apiPath))) return notFoundResponse(request);
  return NextResponse.next();
}

export const config = {
  matcher: [
    "/instituciones/:id",
    "/legislacion/:id",
    "/constitucion/:clave",
    "/aprender/:leccion",
  ],
};
