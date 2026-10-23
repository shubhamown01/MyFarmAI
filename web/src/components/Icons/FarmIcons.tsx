import type { SVGProps, ImgHTMLAttributes } from 'react';

type IconProps = SVGProps<SVGSVGElement>;
type BrandMarkProps = Omit<ImgHTMLAttributes<HTMLImageElement>, 'src' | 'alt'> & {
  /** Optional fallback for environments where the image may not load */
  fallback?: React.ReactNode;
};

/**
 * The small brand mark used in the sidebar and mobile header.
 * Uses the transparent-background MyFarm AI logo asset so it renders correctly
 * on both light and dark themes without a white box around the mark.
 * PNG with WebP fallback; the locked source file is never modified.
 */
export function BrandMark({ className, fallback, ...props }: BrandMarkProps) {
  return (
    <picture {...props}>
      <source srcSet="/images/logo-transparent.webp" type="image/webp" />
      <img
        src="/images/logo-transparent.png"
        alt=""
        className={className}
        width={48}
        height={48}
        decoding="async"
        loading="eager"
      />
      {fallback}
    </picture>
  );
}

/**
 * SVG fallback brand mark (preserved for reference/offline use).
 * Not used in production; the locked PNG/WebP assets are the canonical brand representation.
 */
export function BrandMarkSVG({ className, ...props }: IconProps) {
  return (
    <svg
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      className={className}
      {...props}
    >
      <defs>
        <linearGradient id="brand-leaf-a" x1="9" y1="9" x2="27" y2="29" gradientUnits="userSpaceOnUse">
          <stop stopColor="#7BD96A" />
          <stop offset="1" stopColor="#25943D" />
        </linearGradient>
        <linearGradient id="brand-leaf-b" x1="25" y1="7" x2="43" y2="27" gradientUnits="userSpaceOnUse">
          <stop stopColor="#33B558" />
          <stop offset="1" stopColor="#087A39" />
        </linearGradient>
      </defs>
      <path
        d="M23.2 40.5c0-8.2.1-14.2.1-18.7 0-4.3 1.6-7.2 4.8-9.6"
        stroke="#087A39"
        strokeWidth="3.2"
        strokeLinecap="round"
      />
      <path
        d="M26.1 23.7c-1.5-7.1 2.1-13 9.9-16.2 1.2-.5 2.4-.9 3.7-1.2 1.3 8.2-2.7 14.1-9.8 16.7-1.3.5-2.5.7-3.8.7Z"
        fill="url(#brand-leaf-b)"
      />
      <path
        d="M28.6 21.8c3.2-4.4 6.8-7.1 10.7-9.1"
        stroke="#BDF0BE"
        strokeWidth="1.6"
        strokeLinecap="round"
        opacity=".8"
      />
      <path
        d="M23.3 27c-6.9.4-11.7-1.8-14.2-6.6-1-2-1.5-4.2-1.6-6.7 7.8.2 13.2 3.8 15.2 9.5.5 1.5.7 2.8.6 3.8Z"
        fill="url(#brand-leaf-a)"
      />
      <path
        d="M10.6 15.5c4.1 1.5 7.2 4.1 9.7 8.1"
        stroke="#D9F8CC"
        strokeWidth="1.5"
        strokeLinecap="round"
        opacity=".85"
      />
      <path
        d="M22.6 35.2c-4.9.1-8.4-1.9-10.2-5.7-.7-1.5-1.1-3.2-1.2-5.1 5.7.2 9.6 2.9 11 7.2.3 1.2.4 2.4.4 3.6Z"
        fill="#40BB55"
      />
    </svg>
  );
}

/**
 * The greeting illustration: a young seedling in dark soil with a soft green
 * field behind it. Kept as a local SVG so it never depends on a remote asset.
 */
export function SeedlingIllustration({ className, ...props }: IconProps) {
  return (
    <svg
      viewBox="0 0 240 170"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="A young seedling growing in soil"
      className={className}
      {...props}
    >
      <defs>
        <linearGradient id="seedling-leaf-left" x1="112" y1="101" x2="155" y2="76" gradientUnits="userSpaceOnUse">
          <stop stopColor="#6DCE48" />
          <stop offset="1" stopColor="#A5E56E" />
        </linearGradient>
        <linearGradient id="seedling-leaf-right" x1="159" y1="87" x2="195" y2="44" gradientUnits="userSpaceOnUse">
          <stop stopColor="#3FAE3D" />
          <stop offset="1" stopColor="#8ADD53" />
        </linearGradient>
        <linearGradient id="seedling-soil" x1="132" y1="139" x2="176" y2="165" gradientUnits="userSpaceOnUse">
          <stop stopColor="#8A5936" />
          <stop offset="1" stopColor="#59321E" />
        </linearGradient>
      </defs>

      <path
        d="M83 95C83 52 122 28 166 31c40 3 62 30 57 62-5 34-34 48-74 47-36-1-66-14-66-45Z"
        fill="#F1FAF2"
      />
      <path
        d="M78 120c-8-22 2-43 24-58 17-12 44-13 60 3 15 16 13 42-5 55-22 16-66 20-79 0Z"
        fill="#F8FCF8"
      />
      <path d="M102 91.5c2.2 3.3 5.2 5.3 9.2 6" stroke="#4CBB4D" strokeWidth="3.2" strokeLinecap="round" />
      <path d="M216 108.5c2.6 2 5.7 3 9.3 2.6" stroke="#B9E8B6" strokeWidth="2.4" strokeLinecap="round" />

      <path
        d="M155.8 142.7c.2-21.2.3-43.6.3-58.4"
        stroke="#168239"
        strokeWidth="4.2"
        strokeLinecap="round"
      />
      <path
        d="M156.1 104.2c-8.9-1.9-17.3-6.8-23.7-14.6-2.1-2.6-3.8-5.4-5.1-8.3 11.9-2.9 22.3 1 28.4 10.1 2.4 3.6 3.1 8 0 12.8Z"
        fill="url(#seedling-leaf-left)"
      />
      <path
        d="M156 97c1.7-15.4 11.1-26.3 27.8-32.5 4-1.5 7.8-2.1 11.4-2.1-.5 16.8-9.7 28.7-25.2 33.2-5.2 1.5-9.8 1.9-14 1.4Z"
        fill="url(#seedling-leaf-right)"
      />
      <path
        d="M163.5 88.7c7.2-7.3 14.7-13.9 23.5-18.4"
        stroke="#D6F5B2"
        strokeWidth="2.1"
        strokeLinecap="round"
        opacity=".9"
      />
      <path
        d="M156.1 118.3c-7.5 0-13.8-3.5-18.4-9.9 6.7-3.8 13.6-3.2 18.6 1.9 2.5 2.6 4.2 5.3-.2 8Z"
        fill="#64C54A"
        opacity=".85"
      />

      <path
        d="M96 154.8c10.6-9.6 22.9-15.2 37.7-15.1 15.2.1 28.5 5.2 43.8 15.1H96Z"
        fill="url(#seedling-soil)"
      />
      <path
        d="M108 153.8c5.6-5.9 14-9.5 25.4-9.8 11.6-.3 20.7 2.9 27.8 9.8H108Z"
        fill="#A3653C"
        opacity=".75"
      />
      <path d="M119 149.2c5.4 1.4 10.1 2.2 15.4 2.2 5 0 9.8-.8 14.5-2.4" stroke="#6A3F26" strokeWidth="1.5" strokeLinecap="round" opacity=".7" />
      <circle cx="126" cy="155" r="2.2" fill="#4C2B19" />
      <circle cx="143" cy="152.2" r="1.8" fill="#5E3822" />
      <circle cx="166" cy="156" r="2.4" fill="#472616" />
      <circle cx="155" cy="148.6" r="1.5" fill="#6D442B" />
      <circle cx="112" cy="158.2" r="1.7" fill="#5C3520" />
      <path d="m177 146 5.2 2.4" stroke="#6E442A" strokeWidth="1.8" strokeLinecap="round" opacity=".65" />
    </svg>
  );
}

export function LeafIcon({ className, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" className={className} {...props}>
      <path
        d="M26.8 5.2C18.9 4.5 7 8.1 6.1 19.3c-.3 3.7 2.6 6.6 6.2 6.4 11.4-.7 15.2-12.8 14.5-20.5Z"
        fill="#3EB653"
      />
      <path
        d="M8.1 25.4c3.7-7 8.3-11.5 14.8-15.4"
        stroke="#B9ECA9"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
      <path d="M8.4 25.8 5.2 29" stroke="#25943D" strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  );
}

export function LadybugIcon({ className, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" className={className} {...props}>
      <g stroke="#3A3030" strokeWidth="1.7" strokeLinecap="round">
        <path d="M13.7 20.5h-4M14.5 26.2l-3.7 2.1M16.6 31l-2.4 3.4M26.3 20.5h4M25.5 26.2l3.7 2.1M23.4 31l2.4 3.4" />
      </g>
      <path
        d="M20 9.8c7.3 0 12.4 5.5 12.4 12.5S27.6 35 20 35s-12.4-5.7-12.4-12.7S12.7 9.8 20 9.8Z"
        fill="#E2463E"
      />
      <path d="M20 10v25" stroke="#3A3030" strokeWidth="2.2" />
      <path d="M20 12c-4.3 0-7 2.6-7.2 6.4 3.9 1.5 4.6 4.2 4.2 7.6-.3 2.9.9 5.5 3 8.3" stroke="#F37A70" strokeWidth="2.1" strokeLinecap="round" opacity=".75" />
      <circle cx="20" cy="10.3" r="5.3" fill="#3A3030" />
      <path d="M16.4 6.8c-1.4-1.4-3-2-4.7-1.9M23.6 6.8c1.4-1.4 3-2 4.7-1.9" stroke="#3A3030" strokeWidth="1.8" strokeLinecap="round" />
      <circle cx="14.3" cy="19.2" r="2.2" fill="#3A3030" />
      <circle cx="25.9" cy="19.2" r="2.2" fill="#3A3030" />
      <circle cx="14.3" cy="26.2" r="2.2" fill="#3A3030" />
      <circle cx="25.9" cy="26.2" r="2.2" fill="#3A3030" />
      <circle cx="20" cy="29.5" r="1.9" fill="#3A3030" />
    </svg>
  );
}

export function OpenBookIcon({ className, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" className={className} {...props}>
      <path d="M20 10.6v21" stroke="#5B2BD3" strokeWidth="2.2" strokeLinecap="round" />
      <path
        d="M20 11.2C16.5 8.6 12.3 8 7.5 9.1c-1.5.3-2.4 1.4-2.4 2.9v16.8c0 1.7 1.3 2.8 3 2.5 4.4-.8 8.5-.1 11.9 2.3 3.4-2.4 7.5-3.1 11.9-2.3 1.7.3 3-.8 3-2.5V12c0-1.5-.9-2.6-2.4-2.9-4.8-1.1-9-.5-12.5 2.1Z"
        fill="#7C4DFF"
      />
      <path d="M10 15.2c2.4-.5 4.7-.2 7 1M10 20.2c2.4-.5 4.7-.2 7 1M10 25.2c2.4-.5 4.7-.2 7 1" stroke="#E4DAFF" strokeWidth="1.5" strokeLinecap="round" opacity=".9" />
      <path d="M30 15.2c-2.4-.5-4.7-.2-7 1M30 20.2c-2.4-.5-4.7-.2-7 1" stroke="#D5C6FF" strokeWidth="1.5" strokeLinecap="round" opacity=".8" />
    </svg>
  );
}

export function CloudIcon({ className, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 40 32" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" className={className} {...props}>
      <path
        d="M11.1 27.2h18.1c4.2 0 7.3-3 7.3-6.9 0-3.7-2.8-6.7-6.6-6.9-1-5-5.1-8.4-10.2-8.4-5.7 0-10 3.9-10.5 9.1-3.4.5-5.8 3-5.8 6.3 0 3.8 3.2 6.8 7.7 6.8Z"
        fill="#2F80ED"
      />
      <path d="M12.5 22.7c.2-2.3 1.8-4 4.2-4.3" stroke="#9CC8FF" strokeWidth="1.8" strokeLinecap="round" opacity=".8" />
    </svg>
  );
}

export function SunCloudIcon({ className, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 48 44" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" className={className} {...props}>
      <g stroke="#F6C344" strokeWidth="2.6" strokeLinecap="round">
        <path d="M18.5 4v4.1M7.7 9.1l2.9 2.9M4.5 20.6h4.1M32.5 20.6h-4.1M29.4 9.1l-2.9 2.9M7.7 32.1l2.9-2.9M29.4 32.1l-2.9-2.9" />
      </g>
      <circle cx="18.5" cy="20.6" r="8.1" fill="#F8C84A" />
      <path
        d="M19.1 37.5h18.6c4 0 7-2.9 7-6.6 0-3.6-2.7-6.4-6.3-6.6-1-4.8-4.9-8.1-9.8-8.1-5.4 0-9.6 3.7-10.1 8.7-3.3.5-5.6 2.9-5.6 6.1 0 3.6 3 6.5 6.2 6.5Z"
        fill="#63B7F5"
      />
      <path d="M20.3 31.8c.2-2.1 1.6-3.7 3.8-4" stroke="#B8DEFF" strokeWidth="1.8" strokeLinecap="round" opacity=".9" />
    </svg>
  );
}

export function BarChartIcon({ className, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" className={className} {...props}>
      <rect x="5" y="21" width="8" height="13" rx="2.2" fill="#F6A85B" />
      <rect x="16" y="13" width="8" height="21" rx="2.2" fill="#F2994A" />
      <rect x="27" y="7" width="8" height="27" rx="2.2" fill="#E98224" />
      <path d="M4.8 35.4h30.4" stroke="#F6C9A0" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

export function DocumentIcon({ className, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" className={className} {...props}>
      <path
        d="M9.5 7.5c0-1.8 1.4-3.2 3.2-3.2h9.8l8 8v20.2c0 1.8-1.4 3.2-3.2 3.2H12.7c-1.8 0-3.2-1.4-3.2-3.2V7.5Z"
        fill="#8B5CF6"
      />
      <path d="M22.5 4.3v8h8" fill="#C4B5FD" />
      <path d="M14.5 18.2h11M14.5 23.1h11M14.5 28h7.4" stroke="#F4F0FF" strokeWidth="1.9" strokeLinecap="round" opacity=".95" />
    </svg>
  );
}

interface WeatherSceneProps extends IconProps {
  code: number;
}

/** Filled weather scene used in the compact weather card and forecast rows. */
export function WeatherScene({ code, className, ...props }: WeatherSceneProps) {
  const isClear = code === 0 || code === 1;
  const isPartly = code === 2 || code === 3;
  const isRain = [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82].includes(code);
  const isSnow = [71, 73, 75, 77, 85, 86].includes(code);
  const isStorm = [95, 96, 99].includes(code);
  const isFog = code === 45 || code === 48;

  if (isClear) {
    return (
      <svg viewBox="0 0 72 64" fill="none" aria-hidden="true" className={className} {...props}>
        <g stroke="#F6C344" strokeWidth="3" strokeLinecap="round">
          <path d="M36 5v6M15 13l4.3 4.3M6 34h6M57 34h6M57 13l-4.3 4.3M15 55l4.3-4.3M57 55l-4.3-4.3" />
        </g>
        <circle cx="36" cy="34" r="15" fill="#F8C84A" />
        <circle cx="31" cy="29" r="9" fill="#FFDA6A" opacity=".7" />
      </svg>
    );
  }

  if (isFog) {
    return (
      <svg viewBox="0 0 72 64" fill="none" aria-hidden="true" className={className} {...props}>
        <path d="M14 34h44M10 43h52M18 52h36" stroke="#94A3B8" strokeWidth="4" strokeLinecap="round" />
        <path d="M24 25h24c5 0 8-3 8-7 0-3.5-2.7-6.3-6.3-6.6C48.8 7.2 45 5 40.5 5 35 5 30.8 8.6 30.2 13.5c-4 .3-6.2 2.7-6.2 5.8 0 3.3 2.2 5.7 5 5.7Z" fill="#B7C4D3" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 72 64" fill="none" aria-hidden="true" className={className} {...props}>
      {!isRain && !isSnow && !isStorm && (
        <>
          <g stroke="#F6C344" strokeWidth="2.8" strokeLinecap="round">
            <path d="M25 8v5M9 20l3.8 3.8M4 38h5M46 38h-5M41 20l-3.8 3.8M9 50l3.8-3.8M41 50l-3.8-3.8" />
          </g>
          <circle cx="25" cy="38" r="12" fill="#F8C84A" />
        </>
      )}
      <path
        d="M29 51h26c5.5 0 9.5-4 9.5-9 0-4.9-3.7-8.7-8.6-9-1.4-6.5-6.7-11-13.4-11-7.4 0-13.1 5-13.8 11.8-4.5.7-7.7 4-7.7 8.4 0 4.9 4 8.8 8 8.8Z"
        fill={isStorm ? "#7288A6" : "#63B7F5"}
      />
      {isPartly && <path d="M31 44c.3-3 2.3-5.1 5.2-5.6" stroke="#BFE2FF" strokeWidth="2" strokeLinecap="round" opacity=".9" />}
      {isRain &&
        [31, 43, 55].map((x, index) => (
          <path key={x} d={`M${x} ${58 + (index % 2) * 2}l-2.2 4`} stroke="#2F80ED" strokeWidth="3" strokeLinecap="round" />
        ))}
      {isSnow &&
        [31, 43, 55].map((x, index) => (
          <path key={x} d={`M${x - 4} ${59 + (index % 2) * 2}h8M${x} ${55 + (index % 2) * 2}v8`} stroke="#7DD3FC" strokeWidth="2.2" strokeLinecap="round" />
        ))}
      {isStorm && <path d="M45 56h7l-4 7h5l-9 10 2.5-7H41l4-10Z" fill="#F6C344" />}
    </svg>
  );
}
