using System;
using System.Globalization;
using System.IO;
using System.Text.RegularExpressions;
using Tobii.Interaction;

namespace TobiiEyeTracker4CDataStream2
{
    class Program
    {
        static int Main(string[] args)
        {
            if (args.Length < 1)
            {
                Console.Error.WriteLine("Uso: TobiiEyeTracker4CDataStream.exe P00 [diretorio_coletas]");
                return 1;
            }

            string participantNumber = Regex.Replace(args[0], "^P", "", RegexOptions.IgnoreCase);
            if (!Regex.IsMatch(participantNumber, "^\\d+$"))
            {
                Console.Error.WriteLine("Participante invalido. Use 00, 01, 02... ou P00, P01, P02...");
                return 1;
            }

            string participantLabel = "P" + participantNumber.PadLeft(2, '0');
            string collectionsDirectory = args.Length >= 2
                ? Path.GetFullPath(args[1])
                : Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),
                    "demo",
                    "coletas"
                );
            string participantDirectory = Path.Combine(collectionsDirectory, participantLabel);
            string outputPath = Path.Combine(participantDirectory, "data" + participantLabel + ".txt");

            Directory.CreateDirectory(participantDirectory);
            if (File.Exists(outputPath))
            {
                Console.Error.WriteLine("A coleta ja existe e nao sera sobrescrita:");
                Console.Error.WriteLine(outputPath);
                return 2;
            }

            Console.WriteLine("Participante: " + participantLabel);
            Console.WriteLine("Arquivo: " + outputPath);
            Console.WriteLine("Coleta iniciada. Pressione qualquer tecla para encerrar.");
            Console.WriteLine();

            var host = new Host();
            var gazePointDataStream = host.Streams.CreateGazePointDataStream();

            try
            {
                using (var fileStream = new FileStream(outputPath, FileMode.CreateNew, FileAccess.Write, FileShare.Read))
                using (var writer = new StreamWriter(fileStream))
                {
                    writer.AutoFlush = true;
                    gazePointDataStream.GazePoint((x, y, ts) =>
                    {
                        string now = DateTime.Now.ToString("HH:mm:ss:fff", CultureInfo.InvariantCulture);
                        string point = string.Format(
                            CultureInfo.InvariantCulture,
                            "{0}, {1}, {2}",
                            x,
                            y,
                            now
                        );

                        writer.WriteLine(point);
                        Console.WriteLine(point);
                    });

                    Console.ReadKey(true);
                }
            }
            finally
            {
                host.DisableConnection();
            }

            Console.WriteLine();
            Console.WriteLine("Coleta encerrada e arquivo salvo.");
            return 0;
        }
    }
}
