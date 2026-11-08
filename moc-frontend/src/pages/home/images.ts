// Ảnh minh hoạ (Unsplash, miễn phí). Thay bằng ảnh thật của nhà hàng khi có.
const u = (id: string, w = 1800) =>
  `https://images.unsplash.com/${id}?auto=format&fit=crop&w=${w}&q=75`;

export const HOME_IMAGES = {
  hero: u("photo-1517248135467-4c7edcad34c4"),
  banner: u("photo-1414235077428-338989a2e8c0"),
  welcome: u("photo-1552566626-52f8b828add9", 1100),
  welcomeSmall: u("photo-1504674900247-0877df9cc836", 700),
  why: u("photo-1555396273-367ea4eb4db5", 1100),
};
