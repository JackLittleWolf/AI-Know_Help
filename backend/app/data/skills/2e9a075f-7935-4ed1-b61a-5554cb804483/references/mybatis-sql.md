# MyBatis SQLルール

## 適用対象
- すべての MyBatis XMLマッパーファイル（`*Mapper.xml`）

## ルール

### 1. SELECT文では`SELECT *`を使用しない

**❌ NG**:
```xml
<select id="findById" resultMap="TodoResultMap">
    SELECT * FROM todos WHERE id = #{id}
</select>
```

**✅ OK**:
```xml
<select id="findById" resultMap="TodoResultMap">
    SELECT id, meeting_id, title, description, assignee, due_date,
           priority, status, created_by, created_at, updated_at, ai_generated
    FROM todos 
    WHERE id = #{id}
</select>
```

**理由**:
- パフォーマンスの向上（必要なカラムのみ取得）
- テーブル構造変更時の影響範囲の明確化
- 可読性とメンテナンス性の向上
- インデックスの効率的な使用

### 2. SQLは読みやすくフォーマットする

**✅ OK**:
```xml
<select id="findByMeetingId" resultMap="TodoResultMap">
    SELECT id, meeting_id, title, description, assignee, due_date,
           priority, status, created_by, created_at, updated_at, ai_generated
    FROM todos 
    WHERE meeting_id = #{meetingId} 
      AND status != 'completed'
    ORDER BY due_date ASC, priority DESC
</select>
```

**フォーマット規則**:
- 主要なSQL句は独立した行に配置（SELECT, FROM, WHERE, ORDER BY等）
- カラムリストは適度に改行して見やすく
- WHERE句の条件が複数ある場合は`AND`/`OR`をインデント

### 3. パラメータバインディングを使用する

**❌ NG（SQLインジェクションリスク）**:
```xml
<select id="findByName" resultMap="UserResultMap">
    SELECT * FROM users WHERE name = '${name}'
</select>
```

**✅ OK**:
```xml
<select id="findByName" resultMap="UserResultMap">
    SELECT id, name, email, created_at
    FROM users 
    WHERE name = #{name}
</select>
```

### 4. ResultMapを明示的に定義する

**✅ OK**:
```xml
<resultMap id="TodoResultMap" type="com.meetingtracker.entity.TodoEntity">
    <id column="id" property="id"/>
    <result column="meeting_id" property="meetingId"/>
    <result column="title" property="title"/>
    <result column="description" property="description"/>
    <result column="assignee" property="assignee"/>
    <result column="due_date" property="dueDate"/>
    <result column="priority" property="priority"/>
    <result column="status" property="status"/>
    <result column="created_by" property="createdBy"/>
    <result column="created_at" property="createdAt"/>
    <result column="updated_at" property="updatedAt"/>
    <result column="ai_generated" property="aiGenerated"/>
</resultMap>
```

**利点**:
- カラム名とプロパティ名のマッピングが明確
- スネークケース ↔ キャメルケースの変換が明示的
- 再利用可能

### 5. 動的SQLを適切に使用する

**条件付きWHERE句**:
```xml
<select id="searchTodos" resultMap="TodoResultMap">
    SELECT id, meeting_id, title, description, assignee, due_date,
           priority, status, created_by, created_at, updated_at, ai_generated
    FROM todos
    <where>
        <if test="meetingId != null">
            AND meeting_id = #{meetingId}
        </if>
        <if test="status != null">
            AND status = #{status}
        </if>
        <if test="assignee != null">
            AND assignee = #{assignee}
        </if>
    </where>
    ORDER BY due_date ASC
</select>
```

### 6. INSERTとUPDATEは明示的にカラムを指定

**✅ OK**:
```xml
<insert id="insert">
    INSERT INTO todos (
        id, meeting_id, title, description, assignee, due_date,
        priority, status, ai_generated, created_by, created_at, updated_at
    ) VALUES (
        #{id}, #{meetingId}, #{title}, #{description}, #{assignee}, #{dueDate},
        #{priority}, #{status}, #{aiGenerated}, #{createdBy}, #{createdAt}, #{updatedAt}
    )
</insert>

<update id="update">
    UPDATE todos
    SET title = #{title},
        description = #{description},
        assignee = #{assignee},
        due_date = #{dueDate},
        priority = #{priority},
        status = #{status},
        updated_at = #{updatedAt}
    WHERE id = #{id}
</update>
```

### 7. ページネーションにはLIMIT/OFFSETを使用

```xml
<select id="findWithPagination" resultMap="TodoResultMap">
    SELECT id, meeting_id, title, description, assignee, due_date,
           priority, status, created_by, created_at, updated_at, ai_generated
    FROM todos
    WHERE status = #{status}
    ORDER BY created_at DESC
    LIMIT #{limit} OFFSET #{offset}
</select>
```

### 8. JOINは明示的に記述

```xml
<select id="findTodosWithMeetings" resultMap="TodoWithMeetingResultMap">
    SELECT t.id AS todo_id,
           t.title AS todo_title,
           t.status AS todo_status,
           m.id AS meeting_id,
           m.title AS meeting_title,
           m.date AS meeting_date
    FROM todos t
    INNER JOIN meetings m ON t.meeting_id = m.id
    WHERE t.status = #{status}
    ORDER BY m.date DESC, t.due_date ASC
</select>
```

## パフォーマンス最適化

### インデックスを考慮したWHERE句

```xml
<!-- ✅ OK: インデックスカラムを使用 -->
<select id="findByMeetingId" resultMap="TodoResultMap">
    SELECT id, meeting_id, title, status
    FROM todos
    WHERE meeting_id = #{meetingId}  -- meeting_idにインデックスがある
    ORDER BY due_date ASC
</select>

<!-- ❌ NG: 関数を使用するとインデックスが使えない -->
<select id="findByDate" resultMap="TodoResultMap">
    SELECT id, title, created_at
    FROM todos
    WHERE DATE(created_at) = #{date}  -- インデックスが使えない
</select>

<!-- ✅ OK: 範囲検索でインデックスを使用 -->
<select id="findByDate" resultMap="TodoResultMap">
    SELECT id, title, created_at
    FROM todos
    WHERE created_at >= #{startDate}
      AND created_at < #{endDate}
</select>
```

## チェックリスト

- [ ] すべてのSELECT文でカラムを明示的に指定している
- [ ] SQLが読みやすくフォーマットされている
- [ ] パラメータバインディング（`#{param}`）を使用している
- [ ] ResultMapが適切に定義されている
- [ ] 動的SQLが必要な場合は`<if>`, `<where>`等を使用している
- [ ] INSERT/UPDATE文でカラムを明示的に指定している
- [ ] インデックスを考慮したWHERE句になっている
