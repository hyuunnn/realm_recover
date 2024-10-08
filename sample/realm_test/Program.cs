using Realms;

public class TestClass0 : RealmObject
{
    public int integerValue { get; set; }

    public bool boolValue { get; set; }

    public float floatValue { get; set; }

    public double doubleValue { get; set; }

    public string stringValue { get; set; } = Guid.NewGuid().ToString();

    public DateTimeOffset dateValue { get; set; }
}

public class TestClass1 : RealmObject
{
    public int integerValue { get; set; }

    public bool boolValue { get; set; }

    public float floatValue { get; set; }

    public double doubleValue { get; set; }
}

public class Book : RealmObject
{
    [PrimaryKey]
    public string Id { get; set; } = Guid.NewGuid().ToString();

    public string Title { get; set; }

    public string Author { get; set; }

    public double Price { get; set; }

    // One-to-many relationship
    public IList<TestClass0> TestClass0Items { get;  }
}

class Program
{
    static void Main(string[] args)
    {
        var desktopPath = Environment.GetFolderPath(Environment.SpecialFolder.Desktop);
        var config = new RealmConfiguration(Path.Combine(desktopPath, "test.realm"));

        // Realm 데이터베이스 인스턴스 가져오기
        var realm = Realm.GetInstance(config);

        // 데이터 추가
        realm.Write(() =>
        {

            var book1 = realm.Add(new Book { Title = "C# Programming", Author = "Author A", Price = 29.99 });
            var book2 = realm.Add(new Book { Title = "Learn Realm", Author = "Author B", Price = 19.99 });

            var test = new TestClass0
            {
                integerValue = 42,
                boolValue = true,
                floatValue = 3.14f,
                doubleValue = 1.2345,
                stringValue = "Sample String",
                dateValue = DateTimeOffset.Now
            };

            var testObj0 = realm.Add(test);
            book1.TestClass0Items.Add(test);

            var test2 = new TestClass0
            {
                integerValue = 50,
                boolValue = false,
                floatValue = 3.40f,
                doubleValue = 1.555545,
                stringValue = "Sample String222",
                dateValue = DateTimeOffset.Now - TimeSpan.FromDays(1),
            };

            var testObj2 = realm.Add(test2);
            book1.TestClass0Items.Add(test2);

            var test3 = new TestClass0
            {
                integerValue = 1000,
                boolValue = true,
                floatValue = 55.40f,
                doubleValue = 55.555545,
                stringValue = "Sample String255522",
                dateValue = DateTimeOffset.Now - TimeSpan.FromDays(5),
            };

            var testObj3 = realm.Add(test3);
            book1.TestClass0Items.Add(test3);

            realm.Add(new TestClass1 { integerValue = 123, boolValue = false,  floatValue = 3.333f, doubleValue = 44.4444 });
            realm.Add(new TestClass1 { integerValue = 1234, boolValue = true, floatValue = 3.343f, doubleValue = 44.4114 });
            realm.Add(new TestClass1 { integerValue = 12345, boolValue = false, floatValue = 3.3553f, doubleValue = 44.444411 });
            realm.Add(new TestClass1 { integerValue = 123566, boolValue = false, floatValue = 3.33666f, doubleValue = 44.444999 });

            realm.Add(new Book { Title = "Learn python", Author = "Author c", Price = 20.13 });
            realm.Add(new Book { Title = "Learn C", Author = "Author d", Price = 20.14 });
            realm.Add(new Book { Title = "Learn java", Author = "Author e", Price = 20.15 });
            realm.Add(new Book { Title = "Learn javascript", Author = "Author f", Price = 20.16 });
            realm.Add(new Book { Title = "Learn typescript", Author = "Author g", Price = 20.17 });
        });

        // 데이터 조회
        var testClass0Objects = realm.All<TestClass0>();
        var books = realm.All<Book>();

        Console.WriteLine("All objects of TestClass0 in the database:");
        foreach (var obj in testClass0Objects)
        {
            Console.WriteLine($"Integer: {obj.integerValue}, Bool: {obj.boolValue}, Float: {obj.floatValue}, Double: {obj.doubleValue}, String: {obj.stringValue}, Date: {obj.dateValue}");
        }

        Console.WriteLine("\nAll books in the database:");
        foreach (var book in books)
        {
            Console.WriteLine($"Title: {book.Title}, Author: {book.Author}, Price: {book.Price}");
        }

        // 특정 조건의 데이터 조회
        var expensiveBooks = realm.All<Book>().Where(b => b.Price > 20);
        Console.WriteLine("\nBooks with price greater than 20:");
        foreach (var book in expensiveBooks)
        {
            Console.WriteLine($"Title: {book.Title}, Price: {book.Price}");
        }

        Console.WriteLine($"\nRealm database has been saved to: {config.DatabasePath}");
    }
}
