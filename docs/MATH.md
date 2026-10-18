# The Math Behind the Map

This note explains every formula the project uses, in the order the computation runs. Symbols:

- $L$: the land region (mainland outside the DMZ, mainland, or all land including islands)
- $s_1, \dots, s_n$: store locations
- $d(p, q)$: great-circle distance on the Earth
- $r$: the radius of the circles drawn around every store

## 1. Distance on a sphere

The Earth is treated as a sphere of radius $R = 6371.0088$ km, the IUGG mean radius. For two points with latitudes $\varphi_1, \varphi_2$ and longitude difference $\Delta\lambda$, the haversine formula gives

$$
d = 2R\arcsin\sqrt{\sin^2\frac{\Delta\varphi}{2} + \cos\varphi_1\cos\varphi_2\sin^2\frac{\Delta\lambda}{2}}
$$

The code uses an equivalent form that is easier to index. Each point becomes a unit vector

$$
u = (\cos\varphi\cos\lambda,\ \cos\varphi\sin\lambda,\ \sin\varphi)
$$

and the straight-line chord between two unit vectors, $c = \lVert u_1 - u_2 \rVert$, maps to the arc length

$$
d = 2R\arcsin\frac{c}{2}
$$

Since $c \mapsto 2R\arcsin(c/2)$ is increasing, the nearest store by chord is also the nearest store by great-circle distance. A KD-tree over the 3D unit vectors therefore answers exact nearest-store queries on the sphere.

## 2. When two circles meet

Two circles of radius $r$ around stores $s_i$ and $s_j$, with centers $\ell = \lVert s_i - s_j \rVert$ apart, intersect exactly when

$$
\ell \le 2r
$$

In the plane, the intersection points lie on the perpendicular bisector of the two centers. With midpoint $m = (s_i + s_j)/2$ and unit normal $\hat n$ perpendicular to $s_j - s_i$,

$$
P_\pm = m \pm \sqrt{r^2 - \left(\frac{\ell}{2}\right)^2}\ \hat n
$$

At $r = \ell/2$ the two points coincide at $m$. As $r$ grows they slide outward along the bisector. In the answer view, these are the white dots that travel along the yellow lines.

The page also counts how many pairs of circles overlap. That number is the count of store pairs within $2r$ of each other. Counting every pair at large $r$ takes tens of minutes, so the code counts neighbors for a random sample of $m = 4000$ stores and scales up:

$$
\text{pairs}(r) \approx \frac{n}{2m}\sum_{k \in \text{sample}} \#\{\, j \ne k : d(s_k, s_j) \le 2r \,\}
$$

## 3. Where circles touch: the Voronoi diagram

Once two circles overlap, the set of points that are equally far from both stores is the perpendicular bisector. Over all stores, these bisectors form the Voronoi diagram:

$$
V_i = \{\, p : d(p, s_i) \le d(p, s_j)\ \text{for all } j \,\}
$$

Every point of $L$ belongs to the cell of its nearest store. The yellow lines on the map are cell boundaries, shown only where they are already covered by circles.

## 4. Where three circles meet: the circumcenter

A Voronoi vertex is a point equally far from three stores. It is the circumcenter of the triangle the three stores form, and the distance to them is the circumradius. For a plane triangle with sides $a, b, c$ and area $K$,

$$
R_\triangle = \frac{abc}{4K}
$$

On the sphere there is a neat shortcut. Take the unit vectors $a, b, c$ of three stores. The plane through them cuts the sphere in a circle, and that circle is the set of points equidistant from all three on the sphere. Its center direction is the plane's normal:

$$
\hat o = \frac{(b - a) \times (c - a)}{\lVert (b - a) \times (c - a) \rVert}
$$

flipped if needed so that $\hat o \cdot a > 0$.

To get all Voronoi vertices at once, compute the 3D convex hull of all store unit vectors. Its faces are exactly the spherical Delaunay triangles, and each face's outward normal is a Voronoi vertex. For 49,244 distinct store locations this takes about 0.3 seconds.

## 5. The farthest point

The farthest point from any store is

$$
p^* = \arg\max_{p \in L}\ \min_i\ d(p, s_i), \qquad r^* = \min_i d(p^*, s_i)
$$

It is the center of the **largest empty circle**: the biggest circle centered in $L$ that contains no store. When the map grows the circles, $p^*$ is the last point to be covered, and the radius at that moment is $r^*$.

### Why only two kinds of candidates

Let $f(p) = \min_i d(p, s_i)$. Inside one Voronoi cell, $f$ is the distance to a single store, which has no local maximum in the interior of the cell. So a maximum of $f$ over $L$ must be on the edge of a cell or on the edge of $L$.

- Along a Voronoi edge, $f$ is the distance to two stores at once, which is largest at an end of the edge. So in the interior of $L$ the maximum is at a **Voronoi vertex**.
- On the boundary of $L$, the maximum can be anywhere along the coastline or border. The empty circle simply runs into the sea or the DMZ.

The code checks both:

1. Every Voronoi vertex that lies inside $L$, about 93,000 of them.
2. The boundary of $L$ resampled every 0.0002° (about 20 m), giving 300,000 to 840,000 points.

The largest value wins. For all stores on the mainland outside the DMZ, the answer is a Voronoi vertex in Subi-myeon, Uljin, with $r^* = 19.83$ km to three stores at once. Including islands, the answer is on the coast of Gageodo at $r^* = 92.79$ km.

## 6. How much land is covered

The coverage at radius $r$ is the share of $L$ that lies within some circle:

$$
C(r) = \frac{\left|\, L \cap \bigcup_i B(s_i, r) \,\right|}{|L|}
$$

A point is covered exactly when its nearest-store distance is at most $r$. So the code computes $f(p)$ once for about 1.35 million grid cells of 0.005° latitude (about 556 m). Each cell is weighted by $\cos\varphi$ for its true area. Sorting by distance and taking the cumulative weight gives $C(r)$ for every $r$ at once. For all stores, $C(2.87\ \text{km}) = 50\%$ and $C(10\ \text{km}) = 96.8\%$.

## 7. Drawing it fast: the cell-radius bound

To draw the zoomed-in map, the page builds a distance field at screen resolution. Every visible store writes $\lVert p - s_i \rVert^2$ and its index into the pixels of its disk, keeping the minimum per pixel. Pixels with a minimum of at most $r^2$ are covered. Pixels at most a line width inside $r$ form the rim. Pixels whose neighbor has a different store index are on a Voronoi edge.

Done naively, the work is the total area of all disks, which explodes when thousands of large circles overlap. The fix is a simple observation.

**Lemma.** If pixel $p$'s nearest store is $s_i$, then $p \in V_i$, so $\lVert p - s_i \rVert \le \rho_i$, where $\rho_i$ is the distance from $s_i$ to the farthest vertex of its own cell.

So each store only needs to paint a disk of radius $\min(r, \rho_i)$. The disks of radius $\rho_i$ cover each cell once plus some overlap, so the total work stays at a small multiple of the screen area however large $r$ gets. This took dense zoomed-in frames from about 400 ms to under 100 ms.

## 8. Map projection and its error

The page uses an equirectangular projection centered on latitude 36°:

$$
X = (\lambda - \lambda_0)\cdot 111.320 \cos 36^\circ, \qquad Y = (\varphi_0 - \varphi)\cdot 110.95 \quad \text{(km)}
$$

A true circle of radius $r$ at latitude $\varphi$ becomes an ellipse with horizontal radius $r \cdot \cos 36^\circ / \cos\varphi$. Between latitudes 33° and 38.6°, that factor ranges from about 0.96 to 1.04. The precomputed fields and all reported results use exact great-circle distances. Only the zoomed-in live drawing uses plane circles, so its east–west extents can be off by up to 3 to 4%.
