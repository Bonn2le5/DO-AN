import { ago } from "../lib";

export interface ChatMessage { id: string; from: "customer" | "staff"; text: string; at: string }
export interface Conversation {
  id: string; customer: string; online: boolean; unread: number; status: "open" | "closed"; messages: ChatMessage[];
}
const M = (id: string, from: ChatMessage["from"], text: string, min: number): ChatMessage => ({ id, from, text, at: ago(min) });

export const conversationsSeed: Conversation[] = [
  { id: "cv1", customer: "Nguyễn Lan Anh", online: true, unread: 2, status: "open", messages: [
    M("a1", "customer", "Cho mình hỏi lẩu Thái có phần chay không ạ?", 9),
    M("a2", "staff", "Chào chị, hiện bên em có lẩu nấm chay ạ.", 7),
    M("a3", "customer", "Vậy cho mình đặt thêm 1 phần lẩu nấm nhé", 3),
    M("a4", "customer", "Giao trước 7h tối được không?", 2),
  ] },
  { id: "cv2", customer: "Đỗ Minh Khôi", online: false, unread: 1, status: "open", messages: [
    M("b1", "customer", "Mình đã đặt bàn ngày mai, có thể đổi sang 19:00 không?", 55),
  ] },
  { id: "cv3", customer: "Vũ Ngọc Hân", online: false, unread: 0, status: "open", messages: [
    M("c1", "customer", "Mình muốn huỷ đặt bàn hôm qua, tiền cọc xử lý thế nào?", 60 * 29),
    M("c2", "staff", "Chào chị, bên em sẽ liên hệ qua số điện thoại để làm thủ tục hoàn cọc ạ.", 60 * 28),
  ] },
  { id: "cv4", customer: "Hồ Gia Huy", online: true, unread: 0, status: "closed", messages: [
    M("d1", "customer", "Cảm ơn nhà hàng, món rất ngon!", 60 * 5),
  ] },
];

export const aiOverview = { suggested: 12480, ctr: 18.4, conversion: 6.2 };
export const aiTop = {
  recommended: [["Lẩu Thái hải sản", 1840], ["Bò lúc lắc sốt tiêu", 1522], ["Gỏi cuốn tôm thịt", 1204], ["Bún chả Hà Nội", 980], ["Chè khúc bạch nhãn", 760]],
  viewed: [["Lẩu Thái hải sản", 5210], ["Cơm tấm sườn bì chả", 4488], ["Bò lúc lắc sốt tiêu", 4102], ["Trà đào cam sả", 2950], ["Bún chả Hà Nội", 2711]],
  ordered: [["Cơm tấm sườn bì chả", 268], ["Lẩu Thái hải sản", 241], ["Bò lúc lắc sốt tiêu", 210], ["Bún chả Hà Nội", 190], ["Gỏi cuốn tôm thịt", 156]],
  favorited: [["Lẩu Thái hải sản", 402], ["Chè khúc bạch nhãn", 318], ["Trà đào cam sả", 275], ["Bò lúc lắc sốt tiêu", 240], ["Gỏi cuốn tôm thịt", 190]],
} as const;
export const aiRecent = [
  { user: "Nguyễn Lan Anh", food: "Lẩu Thái hải sản", score: 0.96, reason: "Bạn thường chọn món cay và hải sản" },
  { user: "Trần Minh Tân", food: "Bún chả Hà Nội", score: 0.88, reason: "Khách có khẩu vị tương tự đặt món này nhiều nhất" },
  { user: "Phạm Hoài Thương", food: "Gỏi cuốn tôm thịt", score: 0.91, reason: "Tương tự các món khai vị bạn đã đánh giá 5 sao" },
  { user: "Khách mới", food: "Cơm tấm sườn bì chả", score: 0, reason: "Phổ biến hôm nay" },
];
