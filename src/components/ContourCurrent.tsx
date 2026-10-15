/** Two categories, one visual language: a rising current and accumulated currents.
 * The contours are category marks, never an additional confidence encoding. */
export function ContourCurrent({
  category,
  className = "",
}: {
  category: "drive" | "constructed";
  className?: string;
}) {
  return (
    <svg
      className={`contour-current current-${category} ${className}`}
      viewBox="0 0 24 24"
      role="img"
      aria-label={category === "drive" ? "Drive" : "Constructed value"}
    >
      {category === "drive" ? (
        <>
          <path
            className="current-wash"
            d="M2.3 12.7 C2.3 5.1 8.9 1.8 14.4 5.8 C17.9 8.3 19.3 10.2 22 10.8 Q22.8 11.1 22 11.6 C18 12.3 17.7 17.3 13.7 20.1 C8.3 24 1.9 20.2 2.3 12.7Z"
          />
          <path
            className="current-contour"
            d="M4.1 10 C6.1 5.5 10.3 5.5 13.1 8 M4.9 18 C9.9 21 13.2 16.9 15.2 13.7"
          />
          <path
            className="current-spine"
            d="M3.5 14.2 C7.7 17.2 9.7 13.4 10.6 10.3 C11.6 7.5 13.2 7.7 15.4 9.5 C17.8 11.5 19.8 11.8 22 11.2"
          />
        </>
      ) : (
        <>
          <path
            className="current-wash"
            d="M2.3 7.4 C5.3 2.5 10.2 3.2 14.2 6.1 C17.2 8.3 19.8 8.5 22 7.5 C19 11 13.9 11.8 8.6 9.5 C5.7 8.2 3.8 8 2.3 7.4Z"
          />
          <path
            className="current-wash"
            d="M2.3 12 C7 7.5 11.6 11.5 15.3 12.1 C18.1 12.7 20.4 12.4 22 11.5 C19.1 15.2 14.2 16.5 8.6 14 C5.7 12.8 3.8 12.6 2.3 12Z"
          />
          <path
            className="current-wash"
            d="M2.3 16.8 C7 12.5 11.6 16.8 15.3 17.4 C18.1 18 20.4 17.8 22 16.9 C19.1 20.6 14.2 21.8 8.6 19.4 C5.7 18.2 3.8 17.4 2.3 16.8Z"
          />
          <path
            className="current-contour"
            d="M2.3 7.4 C5.3 2.5 10.2 3.2 14.2 6.1 C17.2 8.3 19.8 8.5 22 7.5 M2.3 16.8 C7 12.5 11.6 16.8 15.3 17.4 C18.1 18 20.4 17.8 22 16.9"
          />
          <path
            className="current-spine"
            d="M2.3 12 C7 7.5 11.6 11.5 15.3 12.1 C18.1 12.7 20.4 12.4 22 11.5"
          />
        </>
      )}
    </svg>
  );
}
