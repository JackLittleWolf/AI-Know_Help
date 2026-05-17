# スレッドセーフティ（単一インスタンスと可変状態）

Spring のデフォルト Bean スコープは **Singleton** のため、同一インスタンスが複数スレッドから同時に利用される。**単一インスタンスかつ可変のインスタンス変数（フィールド）を持つ場合**、並行アクセスで不具合やデータ競合を招く可能性がある。レビュー時に以下をチェックする。

---

## 1. チェック観点

| 条件 | リスク |
|------|--------|
| Bean が **Singleton**（`@Service` / `@Component` 等のデフォルト） | 複数リクエストで同一インスタンスが共有される |
| かつ **可変のインスタンス変数**（`List`・`Map`・ミュータブルオブジェクト・プリミティブの setter で変更するフィールドなど）を持つ | スレッド間で読み書きが競合し、不整合・例外の原因になり得る |

**結論**: Singleton Bean に可変のインスタンス変数を持たせない。状態が必要な場合はスコープの見直しやスレッドローカル・明示的同期で対処する。

---

## 2. NG 例（Singleton + 可変フィールド）

```java
@Service
public class TodoCacheService {
    // 可変のインスタンス変数 → 複数スレッドから同時アクセスで不整合
    private final Map<String, TodoEntity> cache = new HashMap<>();

    public TodoEntity getOrLoad(String id) {
        if (cache.containsKey(id)) {
            return cache.get(id);
        }
        TodoEntity loaded = loadFromDb(id);
        cache.put(id, loaded);  // 並行時に競合
        return loaded;
    }
}
```

```java
@Service
public class RequestContextHolder {
    // リクエストごとの値なのにインスタンス変数 → 他スレッドの値で上書きされ得る
    private String currentUserId;

    public void setCurrentUserId(String userId) {
        this.currentUserId = userId;
    }

    public String getCurrentUserId() {
        return currentUserId;  // 別リクエストのスレッドが書き換えている可能性
    }
}
```

---

## 3. OK 例

**パターン A: インスタンス変数を持たない（ステートレス）**

```java
@Service
public class TodoService {
    private final TodoMapper todoMapper;  // 依存注入された Bean（不変参照）は問題なし

    public TodoResponse getTodo(String id) {
        TodoEntity entity = todoMapper.selectById(id);
        return convertToResponse(entity);
    }
}
```

**パターン B: 不変（immutable）または実質不変のみ保持**

```java
@Service
public class ConfigService {
    private final String apiEndpoint;  // コンストラクタで一度だけ代入、以降変更なし → OK

    public ConfigService(@Value("${api.endpoint}") String apiEndpoint) {
        this.apiEndpoint = apiEndpoint;
    }
}
```

**パターン C: 状態が必要な場合はスコープを変更**

```java
@Service
@Scope(value = WebApplicationContext.SCOPE_REQUEST, proxyMode = ScopedProxyMode.TARGET_CLASS)
public class RequestScopedService {
    private String requestId;  // リクエストごとに別インスタンスのため可変でもよい（要検討）
    // ...
}
```

**パターン D: スレッドローカルでリクエスト単位の値を保持**

```java
@Component
public class RequestContextHolder {
    private static final ThreadLocal<String> CURRENT_USER_ID = new ThreadLocal<>();

    public void setCurrentUserId(String userId) {
        CURRENT_USER_ID.set(userId);
    }

    public String getCurrentUserId() {
        return CURRENT_USER_ID.get();
    }

    public void clear() {  // フィルター等でリクエスト終了時にクリアすること
        CURRENT_USER_ID.remove();
    }
}
```

**パターン E: 共有キャッシュはスレッドセーフな実装を使う**

```java
@Service
public class TodoCacheService {
    private final ConcurrentHashMap<String, TodoEntity> cache = new ConcurrentHashMap<>();

    public TodoEntity getOrLoad(String id) {
        return cache.computeIfAbsent(id, k -> loadFromDb(k));
    }
}
```

---

## 4. レビューチェックリスト

- [ ] `@Service` / `@Component` / `@Controller` 等の **Singleton Bean** に、**可変のインスタンス変数**（`List`・`Map`・setter で変更するフィールドなど）がないか
- [ ] 可変状態が必要な場合、**リクエストスコープ**・**ThreadLocal**・**ConcurrentHashMap** 等の適切な設計になっているか
- [ ] 依存注入される **不変の参照**（`private final TodoMapper todoMapper` など）のみの場合は問題なしと判断してよい
- [ ] **定数**（`private static final` の不変オブジェクト）や、**コンストラクタで一度だけ代入し以降変更しないフィールド**は可変状態に含めない

---

## 5. 参照

- Bean スコープの基本: [spring-boot-best-practices.md](spring-boot-best-practices.md) の「Bean のスコープ」
- 例外処理: [exception-handling.md](exception-handling.md)
