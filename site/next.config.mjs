/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  images: {
    unoptimized: true
  },
  trailingSlash: true,
  // 60s default SIGTERMs static export under CPU contention (multi-lane fleet + sibling floor).
  // 300s/page is generous insurance; pages normally render in <1s.
  staticPageGenerationTimeout: 300,
  // Cap build workers so the export coexists with the sibling floor's work on this shared
  // 16-core box instead of oversubscribing into thrash/OOM (default = nproc spawns ~32 workers).
  experimental: { cpus: 6 }
};

export default nextConfig;
