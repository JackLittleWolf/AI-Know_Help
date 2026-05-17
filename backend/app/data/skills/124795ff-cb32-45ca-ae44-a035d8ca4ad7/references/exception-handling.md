# フロントエンドエラーハンドリング

React/TypeScript フロントエンドにおける API 呼び出しとユーザー向けエラーのエラーハンドリングパターン。

## 基本原則

- **共通 API クライアントを使用** - すべての API 呼び出しは `lib/api-client` を経由
- **一貫したエラー形式** - バックエンドは標準化されたエラーレスポンスを返す
- **ユーザーフレンドリーなメッセージ** - ユーザーに意味のあるエラーを表示
- **適切なエラーバウンダリー** - コンポーネントエラーを適切にキャッチ

## API エラーハンドリング

### 標準エラーレスポンス形式

バックエンドはこの形式でエラーを返す：

```typescript
interface ErrorResponse {
  timestamp: string;
  status: number;
  error: string;
  message: string;
  details?: string[];
}
```

### API クライアントパターン

`lib/api-client` の共通 `apiRequest` 関数を使用：

```typescript
// lib/api-client.ts
export async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || response.statusText);
  }

  return response.json();
}
```

### API 関数パターン

```typescript
// api/meetings.ts
export async function fetchMeetings(): Promise<Meeting[]> {
  try {
    return await apiRequest<Meeting[]>('/meetings');
  } catch (error) {
    // 呼び出し元のコンポーネントにエラーを任せる
    throw error;
  }
}

export async function createMeeting(data: CreateMeetingRequest): Promise<Meeting> {
  return apiRequest<Meeting>('/meetings', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
```

## コンポーネントエラーハンドリング

### React Query の使用

```typescript
// components/MeetingList.tsx
export function MeetingList() {
  const { data: meetings, isLoading, error } = useQuery({
    queryKey: ['meetings'],
    queryFn: fetchMeetings,
  });

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return (
      <ErrorMessage>
        会議の取得に失敗しました: {error.message}
      </ErrorMessage>
    );
  }

  return <div>{/* 会議をレンダリング */}</div>;
}
```

### カスタムフックの使用

```typescript
// hooks/useMeetings.ts
export function useMeetings() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    fetchMeetings()
      .then(setMeetings)
      .catch(setError)
      .finally(() => setIsLoading(false));
  }, []);

  return { meetings, isLoading, error };
}
```

### ミューテーションエラーハンドリング

```typescript
// components/TodoForm.tsx
export function TodoForm() {
  const mutation = useMutation({
    mutationFn: createTodo,
    onSuccess: () => {
      toast.success('TODOを作成しました');
      queryClient.invalidateQueries(['todos']);
    },
    onError: (error: Error) => {
      toast.error(`作成に失敗しました: ${error.message}`);
    },
  });

  const handleSubmit = (data: CreateTodoRequest) => {
    mutation.mutate(data);
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* フォームフィールド */}
      {mutation.isError && (
        <ErrorMessage>{mutation.error.message}</ErrorMessage>
      )}
    </form>
  );
}
```

## エラー表示パターン

### インラインエラーメッセージ

```typescript
// フォームバリデーションやフィールド固有のエラー用
{error && (
  <div className="text-red-600 text-sm mt-1">
    {error.message}
  </div>
)}
```

### トースト通知

```typescript
// アクション後の成功・エラーフィードバック用
import { toast } from 'react-hot-toast';

try {
  await createTodo(data);
  toast.success('TODOを作成しました');
} catch (error) {
  toast.error(`作成に失敗しました: ${error.message}`);
}
```

### エラーバウンダリー

```typescript
// コンポーネントエラーをキャッチする用
import { ErrorBoundary } from 'react-error-boundary';

function ErrorFallback({ error }: { error: Error }) {
  return (
    <div role="alert">
      <p>エラーが発生しました:</p>
      <pre>{error.message}</pre>
    </div>
  );
}

<ErrorBoundary FallbackComponent={ErrorFallback}>
  <MeetingList />
</ErrorBoundary>
```

## 一般的なエラーシナリオ

### 404 Not Found

```typescript
// バックエンドはメッセージ付きで 404 を返す
{
  "status": 404,
  "error": "Not Found",
  "message": "指定された会議が見つかりません"
}

// フロントエンドで表示
if (error?.message.includes('見つかりません')) {
  return <NotFoundMessage>会議が見つかりません</NotFoundMessage>;
}
```

### 400 バリデーションエラー

```typescript
// バックエンドはバリデーションエラーを返す
{
  "status": 400,
  "error": "Bad Request",
  "message": "バリデーションエラー",
  "details": [
    "タイトルは必須です",
    "日付の形式が不正です"
  ]
}

// フロントエンドですべてのエラーを表示
{error?.details?.map((detail, i) => (
  <div key={i} className="text-red-600">{detail}</div>
))}
```

### 502 外部 API エラー

```typescript
// バックエンドは外部 API 失敗を返す
{
  "status": 502,
  "error": "Bad Gateway",
  "message": "AI APIの呼び出しに失敗しました"
}

// フロントエンドでユーザーフレンドリーなメッセージを表示
if (error?.status === 502) {
  return (
    <ErrorMessage>
      AI機能が一時的に利用できません。しばらくしてから再度お試しください。
    </ErrorMessage>
  );
}
```

## レビューチェックリスト

エラーハンドリングをレビューする際：

- [ ] API 呼び出しが共通の `apiRequest` 関数を使用している
- [ ] エラーがキャッチされユーザーに表示される
- [ ] エラーメッセージがユーザーフレンドリー（技術的なスタックトレースではない）
- [ ] API 呼び出し中にローディング状態が表示される
- [ ] ミューテーションに成功フィードバックがある
- [ ] エラーバウンダリーが重要なコンポーネントを保護している
- [ ] ネットワークエラーが適切に処理される
- [ ] バリデーションエラーが特定のフィールド問題を表示する
- [ ] 一時的な失敗に対するリトライロジックがある（該当する場合）
- [ ] デバッグ用のエラーログが実装されている

## 避けるべきアンチパターン

```typescript
// ❌ エラーを黙って飲み込まない
try {
  await fetchMeetings();
} catch (error) {
  // 何もしない - ユーザーはフィードバックを見ない
}

// ❌ 技術的なエラーをユーザーに表示しない
catch (error) {
  alert(error.stack); // 技術的な詳細
}

// ❌ response.ok を無視しない
const response = await fetch('/api/meetings');
const data = await response.json(); // エラーレスポンスかもしれない！

// ❌ API 関数でエラーを処理しない
export async function fetchMeetings() {
  try {
    return await apiRequest('/meetings');
  } catch (error) {
    toast.error(error.message); // コンポーネントで行うべき
    return [];
  }
}
```

## ベストプラクティス

```typescript
// ✅ エラーをコンポーネントにバブルアップさせる
export async function fetchMeetings(): Promise<Meeting[]> {
  return apiRequest<Meeting[]>('/meetings');
}

// ✅ コンポーネントでユーザーフィードバック付きでエラーを処理
const { data, error } = useQuery(['meetings'], fetchMeetings);
if (error) {
  return <ErrorMessage>{error.message}</ErrorMessage>;
}

// ✅ リトライ機能を提供
const { refetch } = useQuery(['meetings'], fetchMeetings);
if (error) {
  return (
    <div>
      <ErrorMessage>{error.message}</ErrorMessage>
      <button onClick={() => refetch()}>再試行</button>
    </div>
  );
}

// ✅ 予期しないエラーにエラーバウンダリーを使用
<ErrorBoundary FallbackComponent={ErrorFallback}>
  <App />
</ErrorBoundary>
```
