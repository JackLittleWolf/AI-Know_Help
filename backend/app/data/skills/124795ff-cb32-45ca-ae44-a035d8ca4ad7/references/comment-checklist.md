# コメント・ドキュメントチェックリスト

React と TypeScript フロントエンドコードのコメントとドキュメントの基準。

## 基本原則

- **日本語で記述**（プロジェクト標準）
- **冗長性を避ける** - コードから明らかなことは書かない
- **「なぜ」に焦点を当てる** - コードは「何を」示し、コメントは「なぜ」を説明する
- **簡潔に** - 1行で十分なことが多い

## コンポーネント

### コンポーネントドキュメント

- [ ] **コンポーネントの目的を先頭に文書化**
  - このコンポーネントは何を表示・担当するか？
  - 名前が自明な場合は省略可

```typescript
// ❌ 悪い例：名前から明らか
/**
 * Meeting card component
 */
export function MeetingCard() { }

// ✅ 良い例：コンテキストを追加
/**
 * 会議一覧で表示する会議カード。クリックで詳細画面に遷移
 */
export function MeetingCard() { }

// ✅ 良い例：自明なのでコメント不要
export function MeetingList() { }
```

### Props ドキュメント

- [ ] **型から明らかでない場合、Props の意味を明確化**
  - 単位、有効な値、または特別な動作を文書化
  - 型のみの Props はコメント不要の場合がある

```typescript
// ❌ 悪い例：冗長
interface MeetingCardProps {
  /** Meeting object */
  meeting: Meeting;
}

// ✅ 良い例：有用な情報を追加
interface MeetingCardProps {
  meeting: Meeting;
  /** 選択時のコールバック。未指定の場合はクリック不可 */
  onSelect?: (id: string) => void;
  /** 表示モード: 'compact' は簡易表示 */
  mode?: 'full' | 'compact';
}
```

## 関数・フック

### 公開関数

- [ ] **公開・エクスポート関数に `@param` と `@returns` 付きの JSDoc**
  - 簡潔な説明を含める
  - 各パラメータを文書化
  - 戻り値を文書化

```typescript
/**
 * 会議一覧を取得する
 * @param filters - フィルター条件（オプション）
 * @returns 会議の配列
 */
export async function fetchMeetings(filters?: MeetingFilters): Promise<Meeting[]> {
  // 実装
}
```

### フック

- [ ] **フックの目的と戻り値を文書化**

```typescript
/**
 * 会議データを取得・管理するフック
 * @returns 会議一覧、ローディング状態、エラー情報
 */
export function useMeetings() {
  // 実装
  return { meetings, isLoading, error };
}
```

### 複雑なロジック

- [ ] **複雑なロジックに説明コメント**
  - なぜこのアプローチを選んだか
  - どの問題を解決するか
  - 自明なロジックにはコメント不要

```typescript
// ✅ 良い例：自明でないロジックを説明
// 議事録が空の場合、AI生成ボタンを無効化
// （空の議事録からはTODOを生成できないため）
const isGenerateDisabled = !meeting.minutes || meeting.minutes.trim() === '';

// ❌ 悪い例：明らかなことを述べている
// Check if minutes is empty
const isEmpty = !meeting.minutes;
```

## React 固有

### useEffect

- [ ] **複雑な effect に目的コメント**
  - なぜ effect が必要か
  - 何がトリガーするか

```typescript
// ✅ 良い例
// 会議IDが変更されたら、関連するTODOを再取得
useEffect(() => {
  if (meetingId) {
    fetchTodos(meetingId);
  }
}, [meetingId]);

// ❌ 悪い例：明らか
// Fetch todos when meetingId changes
useEffect(() => {
  fetchTodos(meetingId);
}, [meetingId]);
```

### カスタムフック

- [ ] **フックの動作と副作用を文書化**

```typescript
/**
 * API呼び出しを管理するフック
 *
 * ローディング状態とエラーハンドリングを自動化。
 * エラー時はトーストで通知を表示する。
 *
 * @param apiCall - 実行するAPI関数
 * @returns データ、ローディング状態、エラー、再実行関数
 */
export function useApiCall<T>(apiCall: () => Promise<T>) {
  // 実装
}
```

### state 定義

- [ ] **state（`useState` / `useReducer`）には簡潔な説明コメントを付与**
  - 管理対象と更新意図を 1 行で記載
  - boolean state は true/false の業務上の意味を記載

```typescript
// ✅ 良い例
/** TODO保存APIの実行中フラグ（true の間は送信ボタンを無効化） */
const [isSubmitting, setIsSubmitting] = useState(false);

/** 編集対象のTODO。null は新規作成モード */
const [editingTodo, setEditingTodo] = useState<Todo | null>(null);
```

## 型・インターフェース

### 型定義

- [ ] **interface/type には用途コメントを付与**
  - export 有無に関係なく、1行で「どこで使う型か」を記載
- [ ] **interface/type の各フィールドに簡潔な説明コメントを付与**
  - 全フィールドを対象とする
  - コメントは 1 行で簡潔にし、型の繰り返しではなく意味・用途を書く

```typescript
// ✅ 良い例
/** TODO 一覧表示と更新で共通利用するDTO */
export interface Todo {
  /** TODOの一意識別子 */
  id: string;
  /** 画面に表示するTODOタイトル */
  title: string;
  /** 優先度（high/medium/low） */
  priority: string;
  /** 完了状態（true の場合は編集不可） */
  completed: boolean;
}
```

## 定数（const）

- [ ] **const フィールドには簡潔な説明コメントを付与**
  - 値そのものではなく、用途・利用場面を記載
  - マジックナンバーの意味を明示

```typescript
// ✅ 良い例
/** TODOタイトル入力の最大文字数 */
const TODO_TITLE_MAX_LENGTH = 80;

/** 一覧画面で表示する1ページあたりの件数 */
const PAGE_SIZE = 20;
```

## コメントすべきでないもの

以下のような冗長なコメントは避ける：

```typescript
// ❌ 明らかなことを述べない
// Get meeting by ID
function getMeetingById(id: string) { }

// ❌ 型情報を繰り返さない
/** String parameter */
function setTitle(title: string) { }

// ❌ フィールドの型をそのまま繰り返さない
interface User {
  /** string */
  name: string;
}

// ❌ フレームワークの慣例を文書化しない
// useState hook for managing state
const [count, setCount] = useState(0);

// ❌ プロジェクト全体のパターンを文書化しない
// Use MessageSource for i18n
const message = t('error.notFound');
```

## レビューチェックリスト

コメントをレビューする際：

- [ ] コンポーネントの目的が明確（または自明）
- [ ] 公開関数に `@param` と `@returns` 付きの JSDoc がある
- [ ] Props の意味が明らかでない場合にコメントがある
- [ ] interface/type に用途コメントがある（export 有無を問わない）
- [ ] interface/type の全フィールドに簡潔な説明コメントがある
- [ ] state（`useState` / `useReducer`）に簡潔な説明コメントがある
- [ ] const フィールドに簡潔な説明コメントがある
- [ ] 複雑なロジックが説明されている
- [ ] 自明でないロジックを持つ useEffect フックが文書化されている
- [ ] カスタムフックが動作と戻り値を文書化している
- [ ] 冗長または明らかなコメントがない
- [ ] すべてのコメントが日本語
- [ ] コメントが「なぜ」を説明し「何を」ではない
