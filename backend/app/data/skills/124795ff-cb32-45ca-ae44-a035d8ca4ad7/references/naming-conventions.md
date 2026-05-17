# フロントエンド命名規約

MinutesTrace プロジェクトの React と TypeScript フロントエンドコードの完全な命名規則。

## ディレクトリ・ファイル構造

| 場所 | 規則 | 例 |
|------|------|-----|
| `api/` | 小文字 .ts | `meetings.ts`, `todos.ts` |
| `components/`, `pages/` | **PascalCase**.tsx | `MeetingCard.tsx`, `MeetingList.tsx` |
| `hooks/` | **use** + camelCase .ts | `useMeetings.ts`, `useTodos.ts` |
| `types/` | index.ts または 用途.ts | `index.ts` |
| `lib/`, `constants/`, `utils/` | camelCase .ts | `api-client.ts`, `config.ts` |

## 命名規則

### コンポーネント・型
- **コンポーネント**：**PascalCase**（例：`MeetingCard`、`TodoList`）
- **Props 型**：`XxxProps`（例：`MeetingCardProps`、`TodoListProps`）
- **型・インターフェース名**：**PascalCase**（例：`Meeting`、`Todo`、`ApiResponse`）

### 変数・関数
- **変数・関数**：**camelCase**（例：`meetingData`、`handleClick`）
- **フック**：`use` で始まる（例：`useMeetings`、`useTodos`、`useApiCall`）
- **定数**：**UPPER_SNAKE_CASE**（例：`API_BASE_URL`、`MAX_RETRIES`）

### API 関数
camelCase で一貫したプレフィックスを使用：
- `fetchXxx` - GET リクエスト（例：`fetchMeetings`、`fetchTodoById`）
- `createXxx` - POST リクエスト（例：`createTodo`、`createMeeting`）
- `updateXxx` - PUT/PATCH リクエスト（例：`updateTodo`、`updateMeetingStatus`）
- `deleteXxx` - DELETE リクエスト（例：`deleteTodo`、`deleteMeeting`）

### ルート（React Router）
- パスは**ケバブケース**を使用
- 例：`/`、`/meetings/:id`、`/my-todos`

### DOM 要素の id
- **形式**：**kebab-case**。パターンは `{ページまたはコンポーネント}-{役割}` または `{ページまたはコンポーネント}-{役割}-{ユニークキー}`（リスト項目等）。
- 例：`login-username`、`meeting-detail-edit-btn`、`meeting-card-${meeting.id}`。
- 詳細は [ui-implementation.md](ui-implementation.md) の「7. 要素の id（命名規則）」を参照。

## 一般的なパターン

### コンポーネントファイル
```typescript
// MeetingCard.tsx
interface MeetingCardProps {
  meeting: Meeting;
  onSelect?: (id: string) => void;
}

export function MeetingCard({ meeting, onSelect }: MeetingCardProps) {
  // コンポーネント実装
}
```

### フックファイル
```typescript
// useMeetings.ts
export function useMeetings() {
  // フック実装
  return { meetings, isLoading, error };
}
```

### API ファイル
```typescript
// meetings.ts
export async function fetchMeetings(): Promise<Meeting[]> {
  // 実装
}

export async function createMeeting(data: CreateMeetingRequest): Promise<Meeting> {
  // 実装
}
```

### 型ファイル
```typescript
// types/index.ts
export interface Meeting {
  id: string;
  title: string;
  date: string;
}

export interface Todo {
  id: string;
  title: string;
  completed: boolean;
}
```

## レビューチェックリスト

コードレビュー時に確認：

- [ ] コンポーネントファイルが PascalCase を使用している
- [ ] フックファイルが `use` で始まり camelCase を使用している
- [ ] API ファイルが小文字を使用している
- [ ] Props インターフェースが `XxxProps` パターンに従っている
- [ ] API 関数が正しいプレフィックス（`fetch`、`create`、`update`、`delete`）を使用している
- [ ] 定数が UPPER_SNAKE_CASE を使用している
- [ ] 変数と関数が camelCase を使用している
- [ ] ルートがケバブケースを使用している
- [ ] ファイル名がデフォルトエクスポート名と一致している
